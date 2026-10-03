"""Chat and conversation repository managing dialogue persistence, sliding window history, and data retention."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatMessage, Conversation
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ChatRepository(BaseRepository[Conversation]):
    """Repository managing Conversation threads and individual ChatMessages."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Conversation, session)

    async def create_conversation(
        self, user_id: uuid.UUID, title: str | None = None
    ) -> Conversation:
        """Create a new conversational thread for a user."""
        convo = Conversation(
            user_id=user_id,
            title=title or "Financial Consultation",
        )
        self.session.add(convo)
        await self.session.flush()
        return convo

    async def get_conversation_for_user(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Conversation | None:
        """Retrieve a conversation ensuring tenant ownership."""
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations_for_user(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> list[Conversation]:
        """List recent conversation threads for a user."""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.created_at))
            .limit(limit)
            .options(selectinload(Conversation.messages))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Erase a conversation and all its messages (cascade delete)."""
        convo = await self.get_conversation_for_user(conversation_id, user_id)
        if not convo:
            return False
        await self.session.delete(convo)
        await self.session.flush()
        return True

    async def create_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        content: str,
        tool_calls: dict[str, Any] | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        latency_ms: int | None = None,
    ) -> ChatMessage:
        """Append a dialogue message turn to a conversation."""
        msg = ChatMessage(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
        )
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def get_message(self, message_id: uuid.UUID, user_id: uuid.UUID) -> ChatMessage | None:
        """Fetch a specific message ensuring tenant isolation."""
        stmt = select(ChatMessage).where(
            ChatMessage.id == message_id, ChatMessage.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_message_feedback(
        self, message_id: uuid.UUID, user_id: uuid.UUID, feedback: int
    ) -> ChatMessage | None:
        """Record user feedback rating on an assistant response."""
        msg = await self.get_message(message_id, user_id)
        if not msg:
            return None
        msg.feedback = feedback
        await self.session.flush()
        return msg

    async def list_recent_messages(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID, limit: int = 20
    ) -> list[ChatMessage]:
        """Fetch recent messages for a conversation ordered chronologically."""
        # Query most recent `limit` messages, then order ascending
        subquery = (
            select(ChatMessage)
            .where(
                ChatMessage.conversation_id == conversation_id,
                ChatMessage.user_id == user_id,
            )
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
            .subquery()
        )
        stmt = select(ChatMessage).from_statement(
            select(subquery).order_by(subquery.c.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def purge_old_messages(self, retention_days: int = 90) -> int:
        """Delete messages older than the retention horizon per security.md §11.1."""
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        stmt = delete(ChatMessage).where(ChatMessage.created_at < cutoff)
        result = await self.session.execute(stmt)
        await self.session.flush()
        deleted_count = int(getattr(result, "rowcount", 0) or 0)
        if deleted_count > 0:
            logger.info("Purged %d chat messages older than %d days", deleted_count, retention_days)
        return deleted_count
