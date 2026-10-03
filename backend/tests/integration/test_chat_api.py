"""Integration tests for Phase 17: Chat API, Conversations & AI Coaching."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Annotated
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.ai.safety.circuit_breaker import (
    GRACEFUL_FALLBACK_TEXT,
    LLMCircuitBreaker,
)
from app.api.deps import get_chat_service, get_db
from app.core.cache import cache_manager
from app.core.config import get_settings
from app.core.rate_limit import lockout_manager, rate_limiter
from app.main import app
from app.models.base import Base
from app.models.chat import ChatMessage
from app.repositories.chat_repo import ChatRepository
from app.services.chat_service import ChatService
from app.services.user_service import UserService


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


def _register_and_login(
    client: TestClient, email: str, name: str, enable_consent: bool = True
) -> tuple[str, str]:
    """Helper registering, authenticating, and optionally enabling AI consent."""
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

    if enable_consent:
        patch_res = client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"consent_ai": True},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["consent_ai"] is True

    return user_id, token


def test_post_chat_streaming(client: TestClient) -> None:
    """Verify POST /chat with stream=True delivers well-formed Server-Sent Events."""
    _, token = _register_and_login(client, "streamer@example.com", "Streamer User")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/v1/chat",
        headers=headers,
        json={"message": "How can I budget better?", "stream": True},
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]

    body = res.text
    assert "event: token" in body
    assert "event: done" in body
    assert "message_id" in body


def test_post_chat_non_streaming(client: TestClient) -> None:
    """Verify POST /chat with stream=False returns standard JSON ChatResponse."""
    _, token = _register_and_login(client, "jsonuser@example.com", "JSON User")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/v1/chat",
        headers=headers,
        json={"message": "What is my spending status?", "stream": False},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "assistant"
    assert "content" in data
    assert len(data["content"]) > 0
    assert data["is_fallback"] is False
    assert "tokens_in" in data
    assert "tokens_out" in data
    assert "latency_ms" in data


def test_chat_consent_disabled_forbidden(client: TestClient) -> None:
    """Verify that user with consent_ai=False receives RFC 7807 403 Forbidden with guidance."""
    _, token = _register_and_login(
        client, "noconsent@example.com", "No Consent User", enable_consent=False
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt chat without granting AI consent
    chat_res = client.post(
        "/api/v1/chat",
        headers=headers,
        json={"message": "Can I afford lunch?", "stream": False},
    )
    assert chat_res.status_code == 403
    problem = chat_res.json()
    assert problem["code"] == "AI_CONSENT_REQUIRED"
    assert "guidance" in problem


def test_chat_circuit_breaker_and_graceful_degradation(client: TestClient) -> None:
    """Verify that when downstream LLM fails, circuit breaker trips and returns fallback without 5xx."""
    _, token = _register_and_login(client, "outage@example.com", "Outage Tester")
    headers = {"Authorization": f"Bearer {token}"}

    # Override get_chat_service with failing agent
    def _failing_chat_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ChatService:
        user_service = UserService(db)
        mock_agent = MagicMock()
        mock_agent.run_turn = AsyncMock(side_effect=RuntimeError("Upstream Provider Offline"))
        mock_agent.prompt_manager = MagicMock()
        mock_agent.prompt_manager.version = "v1.0.0"

        breaker = LLMCircuitBreaker(failure_threshold=1, recovery_timeout=60.0)
        return ChatService(
            session=db,
            agent=mock_agent,
            user_service=user_service,
            circuit_breaker=breaker,
        )

    app.dependency_overrides[get_chat_service] = _failing_chat_service

    # Non-streaming request during failure
    res_non_stream = client.post(
        "/api/v1/chat",
        headers=headers,
        json={"message": "Calculate my savings plan", "stream": False},
    )
    # Must NOT return 500 error!
    assert res_non_stream.status_code == 200
    data = res_non_stream.json()
    assert data["is_fallback"] is True
    assert data["content"] == GRACEFUL_FALLBACK_TEXT

    # Streaming request during failure
    res_stream = client.post(
        "/api/v1/chat",
        headers=headers,
        json={"message": "Calculate my savings plan", "stream": True},
    )
    assert res_stream.status_code == 200
    stream_text = res_stream.text
    assert GRACEFUL_FALLBACK_TEXT in stream_text
    assert '"is_fallback": true' in stream_text

    app.dependency_overrides.pop(get_chat_service, None)


def test_chat_history_and_feedback_flow(client: TestClient) -> None:
    """Verify conversation transcript persistence, history retrieval, and feedback submission."""
    _, token = _register_and_login(client, "feedbacker@example.com", "Feedback Tester")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. First turn
    chat_res1 = client.post(
        "/api/v1/chat",
        headers=headers,
        json={"message": "What is the 50/30/20 rule?", "stream": False},
    )
    assert chat_res1.status_code == 200
    data1 = chat_res1.json()
    message_id = data1["message_id"]
    convo_id = data1["conversation_id"]

    # 2. Get history
    hist_res = client.get("/api/v1/chat/history", headers=headers)
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data["conversations"]) >= 1
    found_convo = hist_data["conversations"][0]
    assert found_convo["id"] == convo_id
    assert found_convo["message_count"] == 2  # user + assistant

    # 3. Post positive feedback (+1)
    fb_res = client.post(
        f"/api/v1/chat/{message_id}/feedback",
        headers=headers,
        json={"feedback": 1},
    )
    assert fb_res.status_code == 200
    assert fb_res.json()["feedback"] == 1
    assert fb_res.json()["status"] == "recorded"


@pytest.mark.asyncio
async def test_retention_purge_and_sliding_window(db_session_factory) -> None:
    """Verify that messages older than retention window are purged by maintenance routine."""
    async with db_session_factory() as session:
        chat_repo = ChatRepository(session)
        user_id = uuid.uuid4()

        # Create conversation
        convo = await chat_repo.create_conversation(user_id=user_id, title="Old Convo")

        # Create old message (100 days old)
        old_msg = ChatMessage(
            id=uuid.uuid4(),
            conversation_id=convo.id,
            user_id=user_id,
            role="user",
            content="Old query from 100 days ago",
            created_at=datetime.now(UTC) - timedelta(days=100),
        )
        session.add(old_msg)

        # Create fresh message (today)
        fresh_msg = ChatMessage(
            id=uuid.uuid4(),
            conversation_id=convo.id,
            user_id=user_id,
            role="user",
            content="Recent query from today",
            created_at=datetime.now(UTC),
        )
        session.add(fresh_msg)
        await session.commit()

        # Execute 90-day retention purge
        purged_count = await chat_repo.purge_old_messages(retention_days=90)
        assert purged_count == 1

        # Verify old message was deleted and fresh message remains
        remaining = await chat_repo.list_recent_messages(convo.id, user_id=user_id, limit=20)
        assert len(remaining) == 1
        assert remaining[0].content == "Recent query from today"
