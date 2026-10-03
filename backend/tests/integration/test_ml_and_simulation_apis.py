"""Integration tests for Phase 14: ML, Forecast & Simulation APIs and Anomaly Pipeline."""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.cache import cache_manager
from app.core.config import get_settings
from app.core.rate_limit import lockout_manager, rate_limiter
from app.financial.engine import (
    calculate_doubling_time,
    calculate_future_value,
    calculate_monthly_required_saving,
    run_scenario,
)
from app.financial.schemas import ScenarioInput
from app.main import app
from app.models.anomaly import Anomaly
from app.models.base import Base
from app.models.feature import MonthlyFeature
from app.models.recommendation import AIRecommendation
from app.models.user import User
from app.services.ml_service import MLService
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

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _register_and_login(client: TestClient, email: str, name: str) -> tuple[str, str]:
    """Helper registering and returning (user_id, token)."""
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": "SecurePassword123!"},
    )
    assert reg_res.status_code == 201
    user_id = reg_res.json()["id"]

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return user_id, token


async def _seed_monthly_features(session_factory, user_id_str: str, months_count: int = 3) -> None:
    """Helper seeding historical monthly features for mature user tests."""
    import uuid

    uid = uuid.UUID(user_id_str)
    months = [date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 1)][:months_count]

    async with session_factory() as session:
        for idx, m in enumerate(months):
            feat = MonthlyFeature(
                user_id=uid,
                month=m,
                income=Decimal("35000.00"),
                expense=Decimal("24000.00") + Decimal(idx * 500),
                savings=Decimal("11000.00"),
                savings_rate=Decimal("31.4285"),
                necessity_expense=Decimal("18000.00"),
                discretionary_expense=Decimal("6000.00"),
                necessity_rate=Decimal("0.7500"),
                discretionary_rate=Decimal("0.2500"),
                txn_count=35,
                cashout_count=2,
                expense_variance=Decimal("450000.00"),
                category_breakdown={"Food": "12000.00", "Bills": "6000.00", "Shopping": "6000.00"},
            )
            session.add(feat)
        await session.commit()


def test_behavior_profile_endpoint_mature_user_and_debounce(
    client: TestClient, db_session_factory
) -> None:
    """Verify behavior profile classification, top factors, model version, and debounce behavior."""
    user_id, token = _register_and_login(client, "profile.user@example.com", "Mature User")
    asyncio.run(_seed_monthly_features(db_session_factory, user_id, months_count=3))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. First fetch triggers classification
    res = client.get("/api/v1/behavior/profile", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == user_id
    assert data["profile"] in (
        "balanced_spender",
        "cash_dominant_transactor",
        "consistent_saver",
        "discretionary_spender",
        "tight_budgeter",
        "volatile_earner",
        "insufficient_data",
    )
    assert Decimal(str(data["confidence"])) >= Decimal("0.0")
    assert "top_factors" in data
    assert data["model_version"] != ""
    assert data["is_cold_start"] is False
    first_created_at = data["created_at"]

    # 2. Second fetch within debounce window returns cached profile
    res2 = client.get("/api/v1/behavior/profile", headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["created_at"].rstrip("Z") == first_created_at.rstrip("Z")
    assert data2["profile"] == data["profile"]

    # 3. Forced refresh re-evaluates
    res_forced = client.get("/api/v1/behavior/profile?force=true", headers=headers)
    assert res_forced.status_code == 200


def test_behavior_profile_cold_start_insufficient_data(client: TestClient) -> None:
    """Verify cold-start user returns INSUFFICIENT_DATA RFC 7807 problem+json with guidance."""
    user_id, token = _register_and_login(client, "coldstart.user@example.com", "Cold Start User")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Default request returns 422 INSUFFICIENT_DATA problem+json
    res = client.get("/api/v1/behavior/profile", headers=headers)
    assert res.status_code == 422
    assert "application/problem+json" in res.headers.get("content-type", "")
    data = res.json()
    assert data["code"] == "INSUFFICIENT_DATA"
    assert "guidance" in data
    assert "2 months" in data["detail"] or "2 months" in data["guidance"]

    # 2. Query with allow_cold_start=true returns 200 with insufficient_data profile
    res_allowed = client.get("/api/v1/behavior/profile?allow_cold_start=true", headers=headers)
    assert res_allowed.status_code == 200
    cold_data = res_allowed.json()
    assert cold_data["profile"] == "insufficient_data"
    assert cold_data["is_cold_start"] is True
    assert Decimal(str(cold_data["confidence"])) == Decimal("0.0")


def test_behavior_insights_endpoint(client: TestClient, db_session_factory) -> None:
    """Verify GET /behavior/insights returns structured coaching insights and recommendations."""
    user_id, token = _register_and_login(client, "insights.user@example.com", "Insights User")
    asyncio.run(_seed_monthly_features(db_session_factory, user_id, months_count=3))
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/behavior/insights", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "profile" in data
    assert "confidence" in data
    assert "insights" in data
    assert len(data["insights"]) > 0

    first_insight = data["insights"][0]
    assert "title" in first_insight
    assert "content" in first_insight
    assert "priority" in first_insight
    assert "type" in first_insight


def test_anomalies_list_and_patch_feedback_and_cross_tenant_isolation(
    client: TestClient, db_session_factory
) -> None:
    """Verify listing anomalies, updating feedback status, and tenant isolation (ASVS L2)."""
    import uuid

    user_a_id, token_a = _register_and_login(client, "user.a.anom@example.com", "User A")
    user_b_id, token_b = _register_and_login(client, "user.b.anom@example.com", "User B")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Seed an anomaly for User A
    anomaly_id = uuid.uuid4()

    async def _seed_anomaly():
        async with db_session_factory() as session:
            anom = Anomaly(
                id=anomaly_id,
                user_id=uuid.UUID(user_a_id),
                scope="transaction",
                category="Shopping",
                anomaly_score=Decimal("0.9200"),
                observed_value=Decimal("45000.00"),
                baseline_value=Decimal("5000.00"),
                deviation_pct=Decimal("800.00"),
                explanation={"message": "Unusually high spending detected in Shopping"},
                model_version="anomaly_detector_v1.0.0",
                status="open",
            )
            session.add(anom)
            await session.commit()

    asyncio.run(_seed_anomaly())

    # 2. User A lists anomalies
    list_res = client.get("/api/v1/anomalies", headers=headers_a)
    assert list_res.status_code == 200
    anomalies = list_res.json()
    assert len(anomalies) == 1
    assert anomalies[0]["id"] == str(anomaly_id)
    assert anomalies[0]["status"] == "open"
    assert anomalies[0]["category"] == "Shopping"

    # 3. User A updates status to dismissed
    patch_res = client.patch(
        f"/api/v1/anomalies/{anomaly_id}",
        headers=headers_a,
        json={"status": "dismissed"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "dismissed"

    # 4. Cross-Tenant Security Check: User B attempts to patch User A's anomaly -> 404 Not Found
    attack_res = client.patch(
        f"/api/v1/anomalies/{anomaly_id}",
        headers=headers_b,
        json={"status": "confirmed"},
    )
    assert attack_res.status_code == 404


def test_forecast_expenses_and_savings_with_uncertainty(
    client: TestClient, db_session_factory
) -> None:
    """Verify expense and savings forecasting with uncertainty bounds and fallback path."""
    user_id, token = _register_and_login(client, "forecast.user@example.com", "Forecast User")
    asyncio.run(_seed_monthly_features(db_session_factory, user_id, months_count=3))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Expense Forecast
    exp_res = client.get("/api/v1/forecast/expenses", headers=headers)
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert "predicted_expense" in exp_data
    assert "lower_bound" in exp_data
    assert "upper_bound" in exp_data
    assert "confidence" in exp_data
    assert "model_version" in exp_data
    assert "assumptions" in exp_data
    assert exp_data["disclaimer_code"] == "PROJECTION_NOT_GUARANTEED"

    p10 = Decimal(str(exp_data["lower_bound"]))
    p50 = Decimal(str(exp_data["predicted_expense"]))
    p90 = Decimal(str(exp_data["upper_bound"]))
    # Monotonicity check
    assert p10 <= p50 <= p90

    # 2. Savings Forecast
    sav_res = client.get("/api/v1/forecast/savings", headers=headers)
    assert sav_res.status_code == 200
    sav_data = sav_res.json()
    assert "projected_income" in sav_data
    assert "predicted_savings" in sav_data
    assert "lower_bound" in sav_data
    assert "upper_bound" in sav_data
    assert "confidence" in sav_data
    assert "assumptions" in sav_data
    assert sav_data["disclaimer_code"] == "PROJECTION_NOT_GUARANTEED"

    # 3. Cold start user returns INSUFFICIENT_DATA
    _, cold_token = _register_and_login(client, "cold.forecast@example.com", "Cold Forecaster")
    cold_headers = {"Authorization": f"Bearer {cold_token}"}
    cold_exp = client.get("/api/v1/forecast/expenses", headers=cold_headers)
    assert cold_exp.status_code == 422
    assert cold_exp.json()["code"] == "INSUFFICIENT_DATA"

    # 4. Cold start with fallback path allowed
    fallback_exp = client.get(
        "/api/v1/forecast/expenses?allow_cold_start=true", headers=cold_headers
    )
    assert fallback_exp.status_code == 200
    assert fallback_exp.json()["fallback_used"] is True


def test_simulation_endpoints_exact_contract_with_financial_engine(client: TestClient) -> None:
    """Verify simulation endpoints match Financial Engine pure calculations exactly (contract test)."""
    _, token = _register_and_login(client, "sim.user@example.com", "Sim User")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Growth Simulation (calculate_future_value)
    p = Decimal("50000.00")
    r = Decimal("0.08")
    y = 5
    pmt = Decimal("5000.00")
    engine_fv = calculate_future_value(
        principal=p,
        annual_rate=r,
        years=y,
        monthly_contribution=pmt,
        compounding_per_year=12,
        contribution_timing="end",
        rate_type="assumed",
    )

    growth_res = client.post(
        "/api/v1/simulate/growth",
        headers=headers,
        json={
            "initial_deposit": str(p),
            "monthly_contribution": str(pmt),
            "annual_rate": str(r),
            "years": y,
            "compounding_per_year": 12,
            "timing": "end",
            "rate_type": "assumed",
        },
    )
    assert growth_res.status_code == 200
    g_data = growth_res.json()
    assert Decimal(str(g_data["future_value"])) == engine_fv.future_value
    assert Decimal(str(g_data["total_contributed"])) == engine_fv.total_contributed
    assert Decimal(str(g_data["total_growth"])) == engine_fv.total_growth
    assert g_data["disclaimer_code"] == "PROJECTION_NOT_GUARANTEED"
    assert g_data["confidence"] == "1.0000"
    assert g_data["model_version"] == "financial_engine_v1.0.0"

    # 2. Goal Simulation (calculate_monthly_required_saving)
    target = Decimal("200000.00")
    curr = Decimal("20000.00")
    months = 24
    engine_goal = calculate_monthly_required_saving(
        target=target,
        current=curr,
        months=months,
        annual_rate=Decimal("0.06"),
        rate_type="contractual",
        contribution_timing="end",
    )

    goal_res = client.post(
        "/api/v1/simulate/goal",
        headers=headers,
        json={
            "target_amount": str(target),
            "current_amount": str(curr),
            "months": months,
            "annual_rate": "0.06",
            "rate_type": "contractual",
        },
    )
    assert goal_res.status_code == 200
    goal_data = goal_res.json()
    assert Decimal(str(goal_data["required_monthly_saving"])) == engine_goal.required_monthly_saving
    assert Decimal(str(goal_data["shortfall"])) == engine_goal.shortfall

    # 3. Doubling Simulation (calculate_doubling_time)
    engine_doubling = calculate_doubling_time(
        annual_rate=Decimal("0.09"),
        compounding_per_year=12,
        rate_type="assumed",
    )

    doubling_res = client.post(
        "/api/v1/simulate/doubling",
        headers=headers,
        json={
            "annual_rate": "0.09",
            "compounding_per_year": 12,
            "rate_type": "assumed",
        },
    )
    assert doubling_res.status_code == 200
    doubling_data = doubling_res.json()
    assert Decimal(str(doubling_data["years"])) == engine_doubling.years
    assert doubling_data["months"] == engine_doubling.months
    assert Decimal(str(doubling_data["rule_of_72_approx"])) == engine_doubling.rule_of_72_approx

    # 4. Scenario Simulation (run_scenario)
    base_in = ScenarioInput(
        initial_balance=Decimal("10000.00"),
        monthly_income=Decimal("40000.00"),
        monthly_expense=Decimal("30000.00"),
        monthly_savings=Decimal("10000.00"),
        annual_return_rate=Decimal("0.05"),
        horizon_years=5,
    )
    sim_overrides = {
        "initial_balance": Decimal("10000.00"),
        "monthly_income": Decimal("40000.00"),
        "monthly_expense": Decimal("25000.00"),
        "monthly_savings": Decimal("15000.00"),
        "annual_return_rate": Decimal("0.08"),
        "horizon_years": 5,
    }
    engine_scen = run_scenario(base=base_in, overrides=sim_overrides)

    scen_res = client.post(
        "/api/v1/simulate/scenario",
        headers=headers,
        json={
            "baseline": {
                "initial_balance": "10000.00",
                "monthly_income": "40000.00",
                "monthly_expense": "30000.00",
                "monthly_savings": "10000.00",
                "annual_return_rate": "0.05",
                "horizon_years": 5,
                "rate_type": "assumed",
            },
            "simulated": {
                "initial_balance": "10000.00",
                "monthly_income": "40000.00",
                "monthly_expense": "25000.00",
                "monthly_savings": "15000.00",
                "annual_return_rate": "0.08",
                "horizon_years": 5,
                "rate_type": "assumed",
            },
        },
    )
    assert scen_res.status_code == 200
    scen_data = scen_res.json()
    assert Decimal(str(scen_data["base_future_value"])) == engine_scen.base_future_value
    assert Decimal(str(scen_data["simulated_future_value"])) == engine_scen.simulated_future_value
    assert Decimal(str(scen_data["net_benefit"])) == engine_scen.net_benefit


def test_end_to_end_outbox_anomaly_pipeline(client: TestClient, db_session_factory) -> None:
    """Verify transaction creation -> outbox -> worker -> anomaly detected -> recommendation stored."""
    user_id, token = _register_and_login(client, "anomaly.flow@example.com", "Anomaly Flow User")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Post an unusually high transaction in Shopping (৳75,000)
    txn_res = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "amount": "75000.00",
            "transaction_type": "expense",
            "category": "Shopping",
            "purpose": "discretionary",
        },
    )
    assert txn_res.status_code == 201

    # 2. Worker drains outbox
    async def _drain():
        async with db_session_factory() as session:
            processed = await drain_outbox(session)
            await session.commit()
            return processed

    processed = asyncio.run(_drain())
    assert processed >= 1

    # 3. Check that an anomaly was persisted in database
    async def _check_anomaly():
        import uuid

        uid = uuid.UUID(user_id)
        async with db_session_factory() as session:
            stmt = select(Anomaly).where(Anomaly.user_id == uid)
            res = await session.execute(stmt)
            return list(res.scalars().all())

    anomalies = asyncio.run(_check_anomaly())
    assert len(anomalies) >= 1
    assert anomalies[0].category == "Shopping"
    assert anomalies[0].observed_value == Decimal("75000.00")

    # 4. Check that an AIRecommendation was stored with source_refs
    async def _check_rec():
        import uuid

        uid = uuid.UUID(user_id)
        async with db_session_factory() as session:
            stmt = select(AIRecommendation).where(AIRecommendation.user_id == uid)
            res = await session.execute(stmt)
            return list(res.scalars().all())

    recs = asyncio.run(_check_rec())
    assert len(recs) >= 1
    assert recs[0].type == "anomaly_alert"
    assert "Shopping" in recs[0].title
    assert recs[0].source_refs is not None
    assert "anomaly_id" in recs[0].source_refs


def test_nightly_batch_job(db_session_factory) -> None:
    """Verify execution of the nightly ML batch job across registered users."""

    async def _run():
        import uuid

        async with db_session_factory() as session:
            # Seed a test user
            u = User(
                id=uuid.uuid4(),
                name="Nightly Batch Target",
                email="nightly@example.com",
                password_hash="argon2id$mocked",
                monthly_income=Decimal("40000.00"),
            )
            session.add(u)
            await session.commit()

            ml_svc = MLService(session)
            stats = await ml_svc.run_nightly_batch_job()
            return stats

    stats = asyncio.run(_run())
    assert stats["users_processed"] >= 1
    assert stats["profiles_updated"] >= 1
    assert stats["forecasts_generated"] >= 2
    assert stats["errors"] == 0
