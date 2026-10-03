"""Integration tests for Financial Goals, Contributions, and Financial Engine analytics."""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.cache import cache_manager
from app.core.config import get_settings
from app.core.rate_limit import lockout_manager, rate_limiter
from app.main import app
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


def _register_and_get_token(client: TestClient, email: str = "goal.tester@example.com") -> str:
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Goal User", "email": email, "password": "SecurePassword123!"},
    )
    assert res.status_code == 201
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    return login_res.json()["access_token"]


def test_goal_lifecycle_and_financial_engine_metrics(client: TestClient) -> None:
    """Test full goal lifecycle: creation, calculation with Financial Engine, contributions, and achievement."""
    token = _register_and_get_token(client, "goals.lifecycle@example.com")
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a goal with initial contribution: Target ৳100,000, initial ৳20,000, target date in 10 months
    target_date = date(datetime.now(UTC).year + 1, 10, 1).isoformat()
    create_res = client.post(
        "/api/v1/goals",
        headers=auth_headers,
        json={
            "name": "Emergency Fund 2027",
            "target_amount": "100000.00",
            "initial_amount": "20000.00",
            "target_date": target_date,
        },
    )
    assert create_res.status_code == 201
    goal = create_res.json()
    goal_id = goal["id"]
    assert goal["name"] == "Emergency Fund 2027"
    assert Decimal(str(goal["target_amount"])) == Decimal("100000.00")
    assert Decimal(str(goal["current_amount"])) == Decimal("20000.00")
    assert Decimal(str(goal["progress_pct"])) == Decimal("0.2000")
    assert Decimal(str(goal["required_monthly_saving"])) > Decimal("0.00")
    assert goal["status"] == "active"

    # 2. Verify initial contribution was created in list of contributions
    contribs_res = client.get(f"/api/v1/goals/{goal_id}/contributions", headers=auth_headers)
    assert contribs_res.status_code == 200
    contribs = contribs_res.json()
    assert len(contribs) == 1
    assert Decimal(str(contribs[0]["amount"])) == Decimal("20000.00")

    # 3. Add an explicit contribution of ৳30,000
    add_res = client.post(
        f"/api/v1/goals/{goal_id}/contributions",
        headers=auth_headers,
        json={"amount": "30000.00"},
    )
    assert add_res.status_code == 201
    assert Decimal(str(add_res.json()["amount"])) == Decimal("30000.00")

    # 4. Fetch updated goal: current_amount should now be ৳50,000, progress 50%
    get_res = client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers)
    assert get_res.status_code == 200
    updated_goal = get_res.json()
    assert Decimal(str(updated_goal["current_amount"])) == Decimal("50000.00")
    assert Decimal(str(updated_goal["progress_pct"])) == Decimal("0.5000")

    # 5. Contribute remaining ৳50,000 to achieve goal
    achieve_res = client.post(
        f"/api/v1/goals/{goal_id}/contributions",
        headers=auth_headers,
        json={"amount": "50000.00"},
    )
    assert achieve_res.status_code == 201

    # Fetch achieved goal
    final_res = client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers)
    assert final_res.status_code == 200
    final_goal = final_res.json()
    assert Decimal(str(final_goal["current_amount"])) == Decimal("100000.00")
    assert Decimal(str(final_goal["progress_pct"])) == Decimal("1.0000")
    assert final_goal["status"] == "achieved"

    # 6. Update goal (PATCH)
    patch_res = client.patch(
        f"/api/v1/goals/{goal_id}",
        headers=auth_headers,
        json={"name": "Completed Emergency Fund"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Completed Emergency Fund"

    # 7. Delete goal
    del_res = client.delete(f"/api/v1/goals/{goal_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # Confirm 404 after deletion
    confirm_del = client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers)
    assert confirm_del.status_code == 404
