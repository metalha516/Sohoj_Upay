"""Conversation manager providing sliding-window context, history summarization, and retention cleanup."""

from __future__ import annotations

import logging
import uuid

from app.ai.llm.client import LLMMessage
from app.models.chat import Conversation
from app.repositories.chat_repo import ChatRepository

logger = logging.getLogger(__name__)

DEFAULT_MAX_RECENT_TURNS = 6  # 6 turns = up to 12 user/assistant messages
DEFAULT_RETENTION_DAYS = 90


class ConversationManager:
    """Coordinates conversation sessions, sliding history window, and context summarization."""

    def __init__(
        self,
        chat_repo: ChatRepository,
        max_recent_turns: int = DEFAULT_MAX_RECENT_TURNS,
        retention_days: int = DEFAULT_RETENTION_DAYS,
    ) -> None:
        self.chat_repo = chat_repo
        self.max_recent_turns = max_recent_turns
        self.retention_days = retention_days

    def auto_generate_title(self, query: str) -> str:
        """Derive a concise conversation title from the opening query."""
        clean = query.strip().split("\n")[0]
        if len(clean) > 50:
            return clean[:47] + "..."
        return clean.capitalize() or "Financial Consultation"

    async def get_or_create_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None = None,
        initial_message: str | None = None,
    ) -> Conversation:
        """Fetch existing conversation or create a new one."""
        if conversation_id:
            convo = await self.chat_repo.get_conversation_for_user(conversation_id, user_id)
            if convo:
                return convo
            logger.info(
                "Conversation %s not found for user %s; generating a new session.",
                conversation_id,
                user_id,
            )

        title = self.auto_generate_title(initial_message) if initial_message else "New Consultation"
        return await self.chat_repo.create_conversation(user_id=user_id, title=title)

    async def build_history_messages(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[LLMMessage]:
        """Build sliding-window dialogue history with compact summarization for older messages."""
        max_messages = self.max_recent_turns * 2
        # Fetch up to 30 recent messages
        raw_messages = await self.chat_repo.list_recent_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=30,
        )

        if not raw_messages:
            return []

        # If history fits comfortably within window, return directly
        if len(raw_messages) <= max_messages:
            return [
                LLMMessage(role=m.role, content=m.content)  # type: ignore[arg-type]
                for m in raw_messages
                if m.role in {"user", "assistant"}
            ]

        # Otherwise, split into older messages for summarization and recent sliding window
        older = raw_messages[:-max_messages]
        recent = raw_messages[-max_messages:]

        summary_parts = []
        for m in older:
            if m.role == "user":
                summary_parts.append(f"User asked: {m.content[:80]}")
            elif m.role == "assistant":
                summary_parts.append(f"Coach addressed: {m.content[:80]}")

        summary_text = (
            "--- PRIOR CONVERSATION RECAP ---\n"
            + "\n".join(summary_parts)
            + "\n--- END PRIOR RECAP ---"
        )

        history: list[LLMMessage] = [
            LLMMessage(role="system", content=summary_text),
        ]
        history.extend(
            [
                LLMMessage(role=m.role, content=m.content)  # type: ignore[arg-type]
                for m in recent
                if m.role in {"user", "assistant"}
            ]
        )
        return history

    async def purge_expired_records(self) -> int:
        """Purge chat messages older than retention policy (90 days)."""
        return await self.chat_repo.purge_old_messages(retention_days=self.retention_days)
