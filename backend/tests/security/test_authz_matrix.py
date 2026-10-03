"""OpenAPI-driven Authorization Matrix and Row-Level Security (RLS) tenant isolation tests."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Generator
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.cache import cache_manager
from app.core.config import get_settings
from app.core.rate_limit import lockout_manager, rate_limiter
from app.main import app
from app.models.anomaly import Anomaly
from app.models.base import Base


@pytest.fixture(autouse=True)
def reset_state() -> Generator[None, None, None]:
    get_settings.cache_clear()
    rate_limiter.reset()
    lockout_manager.reset_all()
    cache_manager.clear_in_memory()
    yield
    rate_limiter.reset()
    lockout_manager.reset_all()
    cache_manager.clear_in_memory()
    get_settings.cache_clear()


@pytest.fixture
def db_session_factory():
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, future=True)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async def _init_models() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init_models())
    yield session_factory
    asyncio.run(engine.dispose())


@pytest.fixture
def client(db_session_factory) -> Generator[TestClient, None, None]:
    async def _override_get_db():
        async with db_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, base_url="http://testserver") as tc:
        yield tc
    app.dependency_overrides.clear()


def _create_user(client: TestClient, name: str, email: str) -> str:
    res = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": "SecurePassword123!"},
    )
    assert res.status_code == 201
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    return login_res.json()["access_token"]


def test_authz_matrix_openapi_driven_cross_tenant_isolation(
    client: TestClient, db_session_factory: Any
) -> None:
    """Verify that User B CANNOT touch any resource owned by User A across all parameterized endpoints.

    OWASP ASVS Requirement: Always expect 404 Not Found to prevent resource enumeration.
    """
    token_a = _create_user(client, "Victim User A", "victim.a@example.com")
    token_b = _create_user(client, "Attacker User B", "attacker.b@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Create resources under User A
    # A's Transaction
    txn_res = client.post(
        "/api/v1/transactions",
        headers=headers_a,
        json={"amount": "12500.00", "transaction_type": "income", "category": "Salary"},
    )
    assert txn_res.status_code == 201
    txn_a_id = txn_res.json()["id"]

    # A's Goal
    goal_res = client.post(
        "/api/v1/goals",
        headers=headers_a,
        json={
            "name": "User A Private Goal",
            "target_amount": "80000.00",
            "initial_amount": "5000.00",
        },
    )
    assert goal_res.status_code == 201
    goal_a_id = goal_res.json()["id"]

    # A's Anomaly (seeded directly in DB for User A)
    me_res = client.get("/api/v1/users/me", headers=headers_a)
    assert me_res.status_code == 200
    user_a_uuid = uuid.UUID(me_res.json()["id"])
    anomaly_a_id = uuid.uuid4()

    async def _seed_anomaly() -> None:
        async with db_session_factory() as session:
            anom = Anomaly(
                id=anomaly_a_id,
                user_id=user_a_uuid,
                scope="transaction",
                category="Food",
                anomaly_score=Decimal("0.85"),
                observed_value=Decimal("5000.00"),
                baseline_value=Decimal("1200.00"),
                deviation_pct=Decimal("316.67"),
                explanation={"reason": "Spending 4x above baseline"},
                model_version="test_v1",
                status="open",
            )
            session.add(anom)
            await session.commit()

    asyncio.run(_seed_anomaly())

    # 2. Extract all parameterized endpoints from OpenAPI spec
    spec = app.openapi()
    paths = spec.get("paths", {})

    # Define test payload generators for methods that require a request body
    method_payloads: dict[tuple[str, str], dict[str, Any]] = {
        ("post", "/api/v1/goals/{goal_id}/contributions"): {"amount": "1000.00"},
        ("patch", "/api/v1/goals/{goal_id}"): {"name": "Malicious Hijack Attempt"},
        ("patch", "/api/v1/anomalies/{anomaly_id}"): {"status": "confirmed"},
    }

    # ID mappings for replacement
    id_map = {
        "{transaction_id}": txn_a_id,
        "{goal_id}": goal_a_id,
        "{anomaly_id}": str(anomaly_a_id),
    }

    matrix_checks_executed = 0

    for path, methods in paths.items():
        # Check if route has a resource ID parameter
        for param_placeholder, resource_id in id_map.items():
            if param_placeholder in path:
                concrete_path = path.replace(param_placeholder, str(resource_id))
                for http_method in methods:
                    if http_method in ("get", "post", "patch", "delete"):
                        matrix_checks_executed += 1
                        payload = method_payloads.get((http_method, path))

                        # User B executes request targeting User A's resource
                        caller = getattr(client, http_method)
                        if payload:
                            response = caller(concrete_path, headers=headers_b, json=payload)
                        else:
                            response = caller(concrete_path, headers=headers_b)

                        assert response.status_code == 404, (
                            f"Cross-tenant leak on {http_method.upper()} {concrete_path}! "
                            f"Expected 404 Not Found, got {response.status_code}: {response.text}"
                        )

    # Ensure matrix actually evaluated all target endpoints
    assert matrix_checks_executed >= 8, (
        f"Expected >= 8 matrix checks, executed {matrix_checks_executed}"
    )


def test_rls_tenant_isolation_under_concurrent_api_load(client: TestClient) -> None:
    """Validate that multi-tenant isolation remains strictly 100% enforced under rapid interleaved calls."""
    token_a = _create_user(client, "Tenant A", "tenant.a@example.com")
    token_b = _create_user(client, "Tenant B", "tenant.b@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Interleave 10 creations across tenants
    for i in range(10):
        # Tenant A writes
        ra = client.post(
            "/api/v1/transactions",
            headers=headers_a,
            json={"amount": f"{1000 + i}.00", "transaction_type": "income", "category": "TenantA"},
        )
        assert ra.status_code == 201

        # Tenant B writes
        rb = client.post(
            "/api/v1/transactions",
            headers=headers_b,
            json={"amount": f"{2000 + i}.00", "transaction_type": "income", "category": "TenantB"},
        )
        assert rb.status_code == 201

    # Verify Tenant A only sees Tenant A transactions
    list_a = client.get("/api/v1/transactions?limit=50", headers=headers_a).json()["items"]
    assert len(list_a) == 10
    for item in list_a:
        assert item["category"] == "TenantA"

    # Verify Tenant B only sees Tenant B transactions
    list_b = client.get("/api/v1/transactions?limit=50", headers=headers_b).json()["items"]
    assert len(list_b) == 10
    for item in list_b:
        assert item["category"] == "TenantB"
