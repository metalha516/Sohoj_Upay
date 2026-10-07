"""Chat service managing end-to-end user dialogues, SSE streaming, persistence, and fail-safes."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agent import AgentTurnResult, FinancialAgent
from app.ai.conversation.manager import ConversationManager
from app.ai.safety.circuit_breaker import (
    GRACEFUL_FALLBACK_TEXT,
    LLMCircuitBreaker,
    TokenBudgetManager,
)
from app.ai.safety.consent_gate import ConsentGate
from app.repositories.chat_repo import ChatRepository
from app.schemas.chat import (
    ChatFeedbackResponse,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    ConversationResponse,
)
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class ChatService:
    """Coordinates dialogue sessions, streaming SSE delivery, persistence, and safety guards."""

    def __init__(
        self,
        session: AsyncSession,
        agent: FinancialAgent,
        user_service: UserService,
        chat_repo: ChatRepository | None = None,
        conversation_mgr: ConversationManager | None = None,
        token_budget_mgr: TokenBudgetManager | None = None,
        circuit_breaker: LLMCircuitBreaker | None = None,
    ) -> None:
        self.session = session
        self.agent = agent
        self.user_service = user_service
        self.chat_repo = chat_repo or ChatRepository(session)
        self.conversation_mgr = conversation_mgr or ConversationManager(self.chat_repo)
        self.token_budget_mgr = token_budget_mgr or TokenBudgetManager()
        self.circuit_breaker = circuit_breaker or LLMCircuitBreaker()
        self.consent_gate = ConsentGate(user_service)

    async def process_chat(
        self,
        user_id: uuid.UUID,
        req: ChatRequest,
    ) -> ChatResponse:
        """Process dialogue turn synchronously without SSE streaming."""
        # 1. Enforce AI consent
        await self.consent_gate.verify_consent(user_id)

        # 2. Check token budget
        await self.token_budget_mgr.check_budget(user_id, estimated_tokens=400)

        # 3. Get or create conversation thread
        convo = await self.conversation_mgr.get_or_create_conversation(
            user_id=user_id,
            conversation_id=req.conversation_id,
            initial_message=req.message,
        )

        # 4. Persist user message
        await self.chat_repo.create_message(
            conversation_id=convo.id,
            user_id=user_id,
            role="user",
            content=req.message,
        )

        # 5. Check circuit breaker status
        if not self.circuit_breaker.can_execute():
            logger.warning("LLM Circuit breaker is OPEN. Emitting graceful degradation response.")
            assistant_msg = await self.chat_repo.create_message(
                conversation_id=convo.id,
                user_id=user_id,
                role="assistant",
                content=GRACEFUL_FALLBACK_TEXT,
                tokens_in=0,
                tokens_out=0,
                latency_ms=1,
            )
            return ChatResponse(
                message_id=assistant_msg.id,
                conversation_id=convo.id,
                role="assistant",
                content=GRACEFUL_FALLBACK_TEXT,
                prompt_version=self.agent.prompt_manager.version,
                is_fallback=True,
                is_grounded=True,
            )

        # 6. Build sliding history
        history = await self.conversation_mgr.build_history_messages(
            conversation_id=convo.id,
            user_id=user_id,
        )

        # 7. Execute agent turn with latency measurement and error recovery
        t0 = time.monotonic()
        try:
            agent_res: AgentTurnResult = await self.agent.run_turn(
                user_id=user_id,
                user_message=req.message,
                conversation_history=history,
            )
            self.circuit_breaker.record_success()
            is_fallback = agent_res.is_fallback
        except Exception as e:
            logger.exception("LLM agent failure encountered: %s", e)
            self.circuit_breaker.record_failure(e)
            agent_res = AgentTurnResult(
                content=GRACEFUL_FALLBACK_TEXT,
                prompt_version=self.agent.prompt_manager.version,
                is_fallback=True,
                is_grounded=True,
            )
            is_fallback = True

        latency_ms = int((time.monotonic() - t0) * 1000)

        # 8. Record token usage
        tokens_est = max(100, len(req.message.split()) * 2 + len(agent_res.content.split()) * 2)
        await self.token_budget_mgr.record_usage(user_id, tokens_est)

        # 9. Persist assistant message turn
        meta_dict: dict[str, Any] = {
            "tools": agent_res.tool_calls_made,
            "data_manifest": agent_res.data_manifest,
            "prompt_version": agent_res.prompt_version,
            "ui_action": agent_res.ui_action,
        }
        assistant_msg = await self.chat_repo.create_message(
            conversation_id=convo.id,
            user_id=user_id,
            role="assistant",
            content=agent_res.content,
            tool_calls=meta_dict,
            tokens_in=len(req.message.split()) * 2,
            tokens_out=len(agent_res.content.split()) * 2,
            latency_ms=latency_ms,
        )

        return ChatResponse(
            message_id=assistant_msg.id,
            conversation_id=convo.id,
            role="assistant",
            content=agent_res.content,
            ui_action=agent_res.ui_action,
            ui_action_payload=agent_res.ui_action_payload,
            tokens_in=assistant_msg.tokens_in or 0,
            tokens_out=assistant_msg.tokens_out or 0,
            latency_ms=latency_ms,
            prompt_version=agent_res.prompt_version,
            is_fallback=is_fallback,
            is_grounded=agent_res.is_grounded,
        )

    async def stream_chat(
        self,
        user_id: uuid.UUID,
        req: ChatRequest,
    ) -> AsyncGenerator[str, None]:
        """Stream conversational turn using Server-Sent Events (SSE).

        Yields events:
        - event: tool_status -> {"tool": "name", "status": "running"|"completed", "call_index": 1}
        - event: token -> {"text": "word/phrase"}
        - event: ui_action -> {"ui_action": "name", "payload": {...}}
        - event: done -> {"message_id": "...", "content": "...", "is_fallback": bool, ...}
        """
        # 1. Enforce AI consent
        await self.consent_gate.verify_consent(user_id)

        # 2. Check token budget
        await self.token_budget_mgr.check_budget(user_id, estimated_tokens=400)

        # 3. Get or create conversation thread
        convo = await self.conversation_mgr.get_or_create_conversation(
            user_id=user_id,
            conversation_id=req.conversation_id,
            initial_message=req.message,
        )

        # 4. Persist user message
        await self.chat_repo.create_message(
            conversation_id=convo.id,
            user_id=user_id,
            role="user",
            content=req.message,
        )

        # 5. Circuit breaker check
        if not self.circuit_breaker.can_execute():
            yield "event: token\ndata: " + json.dumps({"text": GRACEFUL_FALLBACK_TEXT}) + "\n\n"
            assistant_msg = await self.chat_repo.create_message(
                conversation_id=convo.id,
                user_id=user_id,
                role="assistant",
                content=GRACEFUL_FALLBACK_TEXT,
                tokens_in=0,
                tokens_out=0,
                latency_ms=1,
            )
            done_payload = {
                "message_id": str(assistant_msg.id),
                "conversation_id": str(convo.id),
                "content": GRACEFUL_FALLBACK_TEXT,
                "is_fallback": True,
                "is_grounded": True,
            }
            yield "event: done\ndata: " + json.dumps(done_payload) + "\n\n"
            return

        # 6. Build history
        history = await self.conversation_mgr.build_history_messages(
            conversation_id=convo.id,
            user_id=user_id,
        )

        # 7. Execute agent turn
        t0 = time.monotonic()
        try:
            agent_res = await self.agent.run_turn(
                user_id=user_id,
                user_message=req.message,
                conversation_history=history,
            )
            self.circuit_breaker.record_success()
            is_fallback = agent_res.is_fallback
        except Exception as e:
            logger.exception("Streaming LLM failure: %s", e)
            self.circuit_breaker.record_failure(e)
            agent_res = AgentTurnResult(
                content=GRACEFUL_FALLBACK_TEXT,
                prompt_version=self.agent.prompt_manager.version,
                is_fallback=True,
                is_grounded=True,
            )
            is_fallback = True

        latency_ms = int((time.monotonic() - t0) * 1000)

        # 8. Emit tool_status events
        for tc in agent_res.tool_calls_made:
            status_data = {
                "tool": tc.get("tool", "unknown"),
                "status": "completed",
                "call_index": tc.get("call_index", 1),
            }
            yield "event: tool_status\ndata: " + json.dumps(status_data) + "\n\n"

        # 9. Stream validated tokens in chunks
        words = agent_res.content.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i : i + 3]) + (" " if i + 3 < len(words) else "")
            yield "event: token\ndata: " + json.dumps({"text": chunk}) + "\n\n"

        # 10. Emit ui_action if present
        if agent_res.ui_action:
            yield (
                "event: ui_action\ndata: "
                + json.dumps(
                    {"ui_action": agent_res.ui_action, "payload": agent_res.ui_action_payload}
                )
                + "\n\n"
            )

        # 11. Record token usage and persist assistant message
        tokens_est = max(100, len(req.message.split()) * 2 + len(agent_res.content.split()) * 2)
        await self.token_budget_mgr.record_usage(user_id, tokens_est)

        meta_dict = {
            "tools": agent_res.tool_calls_made,
            "data_manifest": agent_res.data_manifest,
            "prompt_version": agent_res.prompt_version,
            "ui_action": agent_res.ui_action,
        }
        assistant_msg = await self.chat_repo.create_message(
            conversation_id=convo.id,
            user_id=user_id,
            role="assistant",
            content=agent_res.content,
            tool_calls=meta_dict,
            tokens_in=len(req.message.split()) * 2,
            tokens_out=len(agent_res.content.split()) * 2,
            latency_ms=latency_ms,
        )

        done_payload = {
            "message_id": str(assistant_msg.id),
            "conversation_id": str(convo.id),
            "content": agent_res.content,
            "tokens_in": assistant_msg.tokens_in or 0,
            "tokens_out": assistant_msg.tokens_out or 0,
            "latency_ms": latency_ms,
            "prompt_version": agent_res.prompt_version,
            "ui_action": agent_res.ui_action,
            "is_fallback": is_fallback,
            "is_grounded": agent_res.is_grounded,
        }
        yield "event: done\ndata: " + json.dumps(done_payload) + "\n\n"

    async def get_history(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> ConversationHistoryResponse:
        """Fetch conversation threads and messages for user."""
        if conversation_id:
            convo = await self.chat_repo.get_conversation_for_user(conversation_id, user_id)
            if not convo:
                return ConversationHistoryResponse(conversations=[])
            convos = [convo]
        else:
            convos = await self.chat_repo.list_conversations_for_user(user_id, limit=limit)

        responses: list[ConversationResponse] = []
        for c in convos:
            msg_responses = [
                ChatMessageResponse(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    role=m.role,
                    content=m.content,
                    feedback=m.feedback,
                    created_at=m.created_at,
                    tool_calls=m.tool_calls,
                )
                for m in (c.messages or [])
            ]
            responses.append(
                ConversationResponse(
                    id=c.id,
                    title=c.title,
                    created_at=c.created_at,
                    message_count=len(msg_responses),
                    messages=msg_responses,
                )
            )
        return ConversationHistoryResponse(conversations=responses)

    async def submit_feedback(
        self,
        user_id: uuid.UUID,
        message_id: uuid.UUID,
        feedback: int,
    ) -> ChatFeedbackResponse:
        """Submit feedback sentiment for an assistant message."""
        msg = await self.chat_repo.update_message_feedback(
            message_id=message_id,
            user_id=user_id,
            feedback=feedback,
        )
        if not msg:
            raise ValueError("Message not found or does not belong to user.")
        return ChatFeedbackResponse(
            message_id=msg.id,
            feedback=feedback,
            status="recorded",
        )
