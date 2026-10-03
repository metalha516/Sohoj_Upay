"""Latency benchmark for dashboard endpoints verifying p95 < 500 ms."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Generator
from datetime import date
from decimal import Decimal

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.cache import cache_manager
from app.core.config import get_settings
from app.core.rate_limit import lockout_manager, rate_limiter
from app.core.security import create_access_token
from app.main import app
from app.models.base import Base
from app.models.feature import MonthlyFeature
from app.models.goal import FinancialGoal
from app.models.user import User


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


def test_dashboard_endpoint_latency_p95_under_500ms(client: TestClient, db_session_factory) -> None:
    """Benchmark GET /api/v1/dashboard verifying p95 latency is strictly under 500 ms."""
    users_count = 50
    user_tokens: list[tuple[str, str]] = []

    # 1. Seed users, monthly features, and goals directly into database
    async def _seed():
        async with db_session_factory() as session:
            for i in range(users_count):
                uid = uuid.uuid4()
                token, _, _ = create_access_token(uid)
                user_tokens.append((str(uid), token))

                user = User(
                    id=uid,
                    name=f"Bench User {i}",
                    email=f"benchmark.user.{i}@example.com",
                    password_hash="argon2id$mocked",
                    monthly_income=Decimal("45000.00"),
                )
                session.add(user)

                feat = MonthlyFeature(
                    user_id=uid,
                    month=date(2026, 3, 1),
                    income=Decimal("45000.00"),
                    expense=Decimal("30000.00"),
                    savings=Decimal("15000.00"),
                    savings_rate=Decimal("33.3333"),
                    necessity_expense=Decimal("20000.00"),
                    discretionary_expense=Decimal("10000.00"),
                    necessity_rate=Decimal("0.6667"),
                    discretionary_rate=Decimal("0.3333"),
                    txn_count=28,
                    cashout_count=2,
                    expense_variance=Decimal("200000.00"),
                    category_breakdown={
                        "Groceries": "12000.00",
                        "Bills": "8000.00",
                        "Dining": "10000.00",
                    },
                )
                session.add(feat)

                goal = FinancialGoal(
                    id=uuid.uuid4(),
                    user_id=uid,
                    name="Benchmark Goal",
                    target_amount=Decimal("100000.00"),
                    current_amount=Decimal("35000.00"),
                    target_date=date(2026, 12, 31),
                    status="active",
                )
                session.add(goal)
            await session.commit()

    asyncio.run(_seed())

    # 2. Measure latencies across 100 requests
    latencies_ms: list[float] = []

    for idx in range(100):
        # Rotate across users
        _, token = user_tokens[idx % len(user_tokens)]
        headers = {"Authorization": f"Bearer {token}"}

        start = time.perf_counter()
        resp = client.get("/api/v1/dashboard", headers=headers)
        duration_ms = (time.perf_counter() - start) * 1000.0

        assert resp.status_code == 200
        latencies_ms.append(duration_ms)

    # 3. Compute percentiles
    p50 = float(np.percentile(latencies_ms, 50))
    p90 = float(np.percentile(latencies_ms, 90))
    p95 = float(np.percentile(latencies_ms, 95))
    p99 = float(np.percentile(latencies_ms, 99))
    max_lat = max(latencies_ms)
    min_lat = min(latencies_ms)

    print("\n--- Dashboard Latency Benchmark Results ---")
    print(f"Total Requests: {len(latencies_ms)}")
    print(f"Min Latency:    {min_lat:.2f} ms")
    print(f"p50 (Median):   {p50:.2f} ms")
    print(f"p90:            {p90:.2f} ms")
    print(f"p95:            {p95:.2f} ms")
    print(f"p99:            {p99:.2f} ms")
    print(f"Max Latency:    {max_lat:.2f} ms")
    print("-------------------------------------------\n")

    # Strict assertion: p95 must be < 500 ms per Phase 14 acceptance criteria
    assert p95 < 500.0, f"Dashboard p95 latency was {p95:.2f} ms, expected < 500 ms"
