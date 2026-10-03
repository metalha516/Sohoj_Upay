"""Pytest configuration and shared test fixtures."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator, Generator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.testclient import TestClient

# Ensure test environment variables are set before loading app
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "false"
os.environ["SECRET_KEY"] = "test_secret_key_at_least_32_characters_long_for_tests"

import app.models  # noqa: F401, E402  # register all models in Base.metadata
from app.api.deps import get_db  # noqa: E402
from app.core.rate_limit import lockout_manager, rate_limiter  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.base import Base  # noqa: E402


@pytest.fixture(autouse=True)
def reset_rate_limiters() -> None:
    """Reset rate limiter and lockout memory stores before each test."""
    rate_limiter.reset()
    lockout_manager.reset_all()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a TestClient instance with an isolated in-memory database."""
    # Shared in-memory SQLite connection for this test
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _init_db() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    loop.run_until_complete(_init_db())

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client

    app.dependency_overrides.clear()

    async def _drop_db() -> None:
        await engine.dispose()

    loop.run_until_complete(_drop_db())
    loop.close()
