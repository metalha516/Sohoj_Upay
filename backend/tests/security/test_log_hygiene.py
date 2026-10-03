"""Tests for log hygiene, structured JSON formatting, and credential scrubbing per security.md §5."""

from __future__ import annotations

import io
import json
import logging
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.config import get_settings
from app.core.logging import JSONFormatter, scrub_message
from app.core.rate_limit import lockout_manager, rate_limiter
from app.main import app
from app.models.base import Base


@pytest.fixture(autouse=True)
def reset_test_state() -> Generator[None, None, None]:
    get_settings.cache_clear()
    rate_limiter.reset()
    lockout_manager.reset_all()
    yield
    rate_limiter.reset()
    lockout_manager.reset_all()
    get_settings.cache_clear()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, future=True)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async def _init_models() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    import asyncio

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

    with TestClient(app, base_url="http://testserver") as tc:
        yield tc

    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def test_scrub_message_unit_patterns() -> None:
    """Validate that scrub_message masks passwords, bearer tokens, emails, and phones."""
    # Password
    sample_pw = '{"password": "UltraSecretPassword123!"}'
    scrubbed_pw = scrub_message(sample_pw)
    assert "UltraSecretPassword123!" not in scrubbed_pw
    assert "[REDACTED]" in scrubbed_pw

    # Bearer Token
    sample_auth = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.secret"
    scrubbed_auth = scrub_message(sample_auth)
    assert "eyJhbGciOiJIUzI1Ni" not in scrubbed_auth
    assert "Bearer [REDACTED]" in scrubbed_auth

    # Email
    sample_email = "User contact email is user.name@sub.domain.bd for communications."
    scrubbed_email = scrub_message(sample_email)
    assert "user.name@sub.domain.bd" not in scrubbed_email
    assert "[REDACTED_EMAIL]" in scrubbed_email

    # Phone (Bangladeshi MFS MSISDN)
    sample_phone = "Sender MSISDN: 01712345678 or +8801812345678"
    scrubbed_phone = scrub_message(sample_phone)
    assert "01712345678" not in scrubbed_phone
    assert "[REDACTED_PHONE]" in scrubbed_phone


def test_auth_request_pipeline_log_hygiene(client: TestClient) -> None:
    """Capture logs during registration and login to verify no sensitive credentials leak to logs."""
    log_stream = io.StringIO()
    stream_handler = logging.StreamHandler(log_stream)
    stream_handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.addHandler(stream_handler)
    original_level = root_logger.level
    root_logger.setLevel(logging.INFO)

    secret_password = "SuperSecretPassword123!"
    secret_email = "hygiene.candidate@example.com"

    try:
        # 1. Register
        reg_res = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Hygiene Test User",
                "email": secret_email,
                "password": secret_password,
            },
        )
        assert reg_res.status_code == 201

        # 2. Login
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": secret_email, "password": secret_password},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]

        # 3. Authenticated me request
        me_res = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200

        # Collect captured log text
        stream_handler.flush()
        captured_logs = log_stream.getvalue()

        # Parse every line as valid JSON and inspect
        for line in captured_logs.strip().splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            # Structured attributes check
            assert "timestamp" in entry
            assert "level" in entry
            assert "message" in entry

            message = entry["message"]
            # Assert credentials never appear in message
            assert secret_password not in message, f"Plaintext password leaked in log: {line}"
            assert token not in message, f"Plaintext JWT leaked in log: {line}"
            # Ensure email is either not present or properly scrubbed
            if secret_email in message:
                pytest.fail(f"Plaintext email leaked in log: {line}")

    finally:
        root_logger.removeHandler(stream_handler)
        root_logger.setLevel(original_level)
