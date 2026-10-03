"""OpenAPI documentation validation and Schemathesis property-based fuzz testing.

Ensures all auth and user endpoints are fully documented and return zero 5xx server errors.
"""

from __future__ import annotations

import asyncio
from collections.abc import Generator

import pytest
import schemathesis
from hypothesis import HealthCheck, settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.rate_limit import lockout_manager, rate_limiter
from app.main import app
from app.models.base import Base

# -----------------------------------------------------------------------------
# Fixtures & Database Overrides for Fuzz Testing
# -----------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def setup_test_engine():
    """Setup shared in-memory SQLite database for Schemathesis ASGI execution."""
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, future=True)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async def _init_models() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init_models())

    async def _override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


@pytest.fixture(autouse=True)
def reset_rate_limits() -> Generator[None, None, None]:
    """Reset rate limiter and account lockout states between test cases."""
    rate_limiter.reset()
    lockout_manager.reset_all()
    yield
    rate_limiter.reset()
    lockout_manager.reset_all()


# -----------------------------------------------------------------------------
# 1. OpenAPI Specification Contract Tests
# -----------------------------------------------------------------------------


def test_openapi_contract_documentation() -> None:
    """Verify that all auth and user endpoints are declared in the OpenAPI specification."""
    openapi_spec = app.openapi()
    paths = openapi_spec.get("paths", {})

    expected_endpoints = [
        ("/api/v1/auth/register", "post"),
        ("/api/v1/auth/login", "post"),
        ("/api/v1/auth/refresh", "post"),
        ("/api/v1/auth/logout", "post"),
        ("/api/v1/auth/change-password", "post"),
        ("/api/v1/users/me", "get"),
        ("/api/v1/users/me", "patch"),
        ("/api/v1/users/me/export", "get"),
        ("/api/v1/users/me", "delete"),
        ("/api/v1/transactions", "post"),
        ("/api/v1/transactions", "get"),
        ("/api/v1/transactions/{transaction_id}", "get"),
        ("/api/v1/transactions/{transaction_id}", "delete"),
        ("/api/v1/cashouts", "post"),
        ("/api/v1/cashouts", "get"),
        ("/api/v1/goals", "post"),
        ("/api/v1/goals", "get"),
        ("/api/v1/goals/{goal_id}", "get"),
        ("/api/v1/goals/{goal_id}", "patch"),
        ("/api/v1/goals/{goal_id}", "delete"),
        ("/api/v1/goals/{goal_id}/contributions", "post"),
        ("/api/v1/goals/{goal_id}/contributions", "get"),
        ("/api/v1/dashboard", "get"),
        ("/api/v1/dashboard/monthly", "get"),
        ("/api/v1/dashboard/categories", "get"),
    ]

    for path, method in expected_endpoints:
        assert path in paths, f"Missing endpoint in OpenAPI: {path}"
        assert method in paths[path], f"Missing HTTP method {method.upper()} for {path}"
        endpoint_def = paths[path][method]
        assert "responses" in endpoint_def
        assert "summary" in endpoint_def
        assert "tags" in endpoint_def

    # Verify security definitions
    components = openapi_spec.get("components", {})
    security_schemes = components.get("securitySchemes", {})
    assert "HTTPBearer" in security_schemes or any(
        s.get("type") == "http" and s.get("scheme") == "bearer" for s in security_schemes.values()
    )


# -----------------------------------------------------------------------------
# 2. Schemathesis Property-Based API Conformance
# -----------------------------------------------------------------------------

schema = schemathesis.openapi.from_asgi("/openapi.json", app).include(
    tag=["Authentication", "Users", "Transactions", "Goals", "Dashboard"]
)


@schema.parametrize()
@settings(
    max_examples=5,
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.filter_too_much,
        HealthCheck.function_scoped_fixture,
    ],
    deadline=None,
)
def test_schemathesis_zero_5xx_server_errors(case: schemathesis.Case) -> None:
    """Property test that automatically generates conforming and non-conforming inputs.

    Verifies that the server NEVER returns a 5xx Internal Server Error on any input.
    """
    response = case.call()
    case.validate_response(response, checks=(schemathesis.checks.not_a_server_error,))
