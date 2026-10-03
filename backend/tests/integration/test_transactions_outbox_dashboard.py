"""Integration tests for Transactions, Cash-outs, Outbox Worker, and Dashboard caching."""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.cache import cache_manager
from app.core.config import get_settings
from app.core.rate_limit import lockout_manager, rate_limiter
from app.main import app
from app.models.base import Base
from app.models.feature import MonthlyFeature
from app.models.outbox import OutboxEvent
from app.worker.outbox_worker import drain_outbox


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


def _register_and_get_token(client: TestClient, email: str = "txn.tester@example.com") -> str:
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Transaction User", "email": email, "password": "SecurePassword123!"},
    )
    assert res.status_code == 201
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    return login_res.json()["access_token"]


# -----------------------------------------------------------------------------
# 1. Validation & Purpose Whitelist Tests
# -----------------------------------------------------------------------------


def test_transaction_purpose_validation(client: TestClient) -> None:
    """Purpose is strictly mandatory for expense and cash_out, optional for income."""
    token = _register_and_get_token(client, "validation@example.com")
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Expense without purpose fails (422)
    r1 = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={"amount": "1500.00", "transaction_type": "expense", "category": "Food"},
    )
    assert r1.status_code == 422
    assert "purpose" in str(r1.json()).lower()

    # Cash-out without purpose fails (422)
    r2 = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={"amount": "2000.00", "transaction_type": "cash_out"},
    )
    assert r2.status_code == 422
    assert "purpose" in str(r2.json()).lower()

    # Dedicated /cashouts endpoint without purpose fails (422)
    r3 = client.post(
        "/api/v1/cashouts",
        headers=auth_headers,
        json={"amount": "2000.00"},
    )
    assert r3.status_code == 422

    # Income without purpose succeeds (201)
    r4 = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={"amount": "50000.00", "transaction_type": "income", "category": "Salary"},
    )
    assert r4.status_code == 201
    assert r4.json()["amount"] == "50000.00"


# -----------------------------------------------------------------------------
# 2. Idempotency Tests
# -----------------------------------------------------------------------------


def test_transaction_idempotency_prevention(client: TestClient) -> None:
    """Submitting the same idempotency key returns the original transaction without duplication."""
    token = _register_and_get_token(client, "idempotent@example.com")
    auth_headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "amount": "3500.00",
        "transaction_type": "expense",
        "purpose": "necessity",
        "category": "Groceries",
        "idempotency_key": "idemp-unique-12345",
    }

    # First attempt: 201 Created
    r1 = client.post("/api/v1/transactions", headers=auth_headers, json=payload)
    assert r1.status_code == 201
    txn1 = r1.json()

    # Second attempt with same key: 200 OK returning same transaction
    r2 = client.post("/api/v1/transactions", headers=auth_headers, json=payload)
    assert r2.status_code == 200
    txn2 = r2.json()
    assert txn1["id"] == txn2["id"]
    assert txn1["amount"] == txn2["amount"]

    # Header-based Idempotency-Key
    header_payload = {
        "amount": "1200.00",
        "purpose": "discretionary",
    }
    r3 = client.post(
        "/api/v1/cashouts",
        headers={**auth_headers, "Idempotency-Key": "header-idemp-999"},
        json=header_payload,
    )
    assert r3.status_code == 201
    txn3 = r3.json()

    r4 = client.post(
        "/api/v1/cashouts",
        headers={**auth_headers, "Idempotency-Key": "header-idemp-999"},
        json=header_payload,
    )
    assert r4.status_code == 200
    assert r4.json()["id"] == txn3["id"]


# -----------------------------------------------------------------------------
# 3. Cursor Pagination Tests
# -----------------------------------------------------------------------------


def test_transaction_cursor_pagination(client: TestClient) -> None:
    """Validate deterministic cursor pagination across 15 transactions."""
    token = _register_and_get_token(client, "pagination@example.com")
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Create 15 transactions
    for i in range(15):
        client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json={
                "amount": f"{100 + i}.00",
                "transaction_type": "income",
                "category": f"Source {i}",
            },
        )

    # Page 1: limit 5
    p1 = client.get("/api/v1/transactions?limit=5", headers=auth_headers)
    assert p1.status_code == 200
    data1 = p1.json()
    assert len(data1["items"]) == 5
    assert data1["has_more"] is True
    cursor1 = data1["next_cursor"]
    assert cursor1 is not None

    # Page 2: limit 5 with cursor
    p2 = client.get(f"/api/v1/transactions?limit=5&cursor={cursor1}", headers=auth_headers)
    assert p2.status_code == 200
    data2 = p2.json()
    assert len(data2["items"]) == 5
    assert data2["has_more"] is True

    # Ensure no overlap between page 1 and page 2
    ids_p1 = {t["id"] for t in data1["items"]}
    ids_p2 = {t["id"] for t in data2["items"]}
    assert len(ids_p1.intersection(ids_p2)) == 0


# -----------------------------------------------------------------------------
# 4. End-to-End Core Product Loop: Cash-out -> Outbox -> Worker -> Dashboard
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_end_to_end_cashout_worker_dashboard_flow(
    client: TestClient, db_session_factory
) -> None:
    """Full loop: create cash-out & income -> worker processes outbox -> dashboard reflects changes."""
    token = _register_and_get_token(client, "e2e.flow@example.com")
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 1. Post Income (৳40,000)
    now_ts = datetime.now(UTC).isoformat()
    r_inc = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "amount": "40000.00",
            "transaction_type": "income",
            "category": "Salary",
            "ts": now_ts,
        },
    )
    assert r_inc.status_code == 201

    # 2. Post Cash-out (৳5,000, necessity)
    r_cash = client.post(
        "/api/v1/cashouts",
        headers=auth_headers,
        json={
            "amount": "5000.00",
            "purpose": "necessity",
            "category": "Cash Out",
            "ts": now_ts,
        },
    )
    assert r_cash.status_code == 201

    # 3. Post Savings Transfer (৳10,000, savings_goal)
    r_sav = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "amount": "10000.00",
            "transaction_type": "transfer",
            "purpose": "savings_goal",
            "category": "DPS Deposit",
            "ts": now_ts,
        },
    )
    assert r_sav.status_code == 201

    # 4. Verify Outbox Events accumulated in DB with processed_at IS NULL
    async with db_session_factory() as session:
        events = (await session.execute(select(OutboxEvent))).scalars().all()
        assert len(events) >= 3
        for ev in events:
            assert ev.processed_at is None

    # 5. Run Worker Drain Cycle
    async with db_session_factory() as session:
        processed_count = await drain_outbox(session)
        assert processed_count >= 3

    # 6. Verify Outbox Events are now processed
    async with db_session_factory() as session:
        events_after = (await session.execute(select(OutboxEvent))).scalars().all()
        for ev in events_after:
            assert ev.processed_at is not None

        # Verify MonthlyFeature row exists in DB
        features = (await session.execute(select(MonthlyFeature))).scalars().all()
        assert len(features) >= 1
        current_feat = features[0]
        assert current_feat.income == Decimal("40000.00")
        assert current_feat.expense == Decimal("5000.00")
        assert current_feat.savings == Decimal("10000.00")
        assert current_feat.cashout_count >= 1

    # 7. Verify Dashboard reflects the updated metrics
    dash_res = client.get("/api/v1/dashboard", headers=auth_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert Decimal(str(dash_data["income"])) == Decimal("40000.00")
    assert Decimal(str(dash_data["expense"])) == Decimal("5000.00")
    assert Decimal(str(dash_data["savings"])) == Decimal("10000.00")

    # 8. Verify Categories endpoint reflects the cash-out
    cat_res = client.get("/api/v1/dashboard/categories", headers=auth_headers)
    assert cat_res.status_code == 200
    cat_data = cat_res.json()
    assert Decimal(str(cat_data["total_expense"])) == Decimal("5000.00")
    assert Decimal(str(cat_data["necessity_expense"])) == Decimal("5000.00")


# -----------------------------------------------------------------------------
# 5. Worker Down Resilience Test
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_worker_down_resilience_and_restart(client: TestClient, db_session_factory) -> None:
    """When the worker is down, the API remains fully operational; events process upon worker restart."""
    token = _register_and_get_token(client, "resilience@example.com")
    auth_headers = {"Authorization": f"Bearer {token}"}

    # API operates normally while worker is offline
    r1 = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={"amount": "25000.00", "transaction_type": "income", "category": "Contract"},
    )
    r2 = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "amount": "8000.00",
            "transaction_type": "expense",
            "purpose": "discretionary",
            "category": "Shopping",
        },
    )
    assert r1.status_code == 201
    assert r2.status_code == 201

    # Verify pending state
    async with db_session_factory() as session:
        unprocessed = (
            (await session.execute(select(OutboxEvent).where(OutboxEvent.processed_at.is_(None))))
            .scalars()
            .all()
        )
        assert len(unprocessed) == 2

    # Worker starts up / runs
    async with db_session_factory() as session:
        drained = await drain_outbox(session)
        assert drained == 2

    # All events are cleared
    async with db_session_factory() as session:
        pending = (
            (await session.execute(select(OutboxEvent).where(OutboxEvent.processed_at.is_(None))))
            .scalars()
            .all()
        )
        assert len(pending) == 0
