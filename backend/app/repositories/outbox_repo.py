"""Repository for transactional outbox queue management."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox import OutboxEvent


class OutboxRepository:
    """Manages transactional outbox events to ensure reliable at-least-once delivery."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_event(
        self,
        aggregate_id: uuid.UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> OutboxEvent:
        """Persist an outbox event in the same transaction as the domain aggregate."""
        event = OutboxEvent(
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(UTC),
            processed_at=None,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_unprocessed_events(self, limit: int = 50) -> Sequence[OutboxEvent]:
        """Fetch pending outbox events ordered chronologically."""
        query = (
            select(OutboxEvent)
            .where(OutboxEvent.processed_at.is_(None))
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def mark_processed(self, event_id: int) -> None:
        """Mark an outbox event as successfully processed."""
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(processed_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def count_unprocessed(self) -> int:
        """Count the number of unprocessed events remaining in the outbox queue."""
        query = select(func.count(OutboxEvent.id)).where(OutboxEvent.processed_at.is_(None))
        result = await self.session.execute(query)
        return result.scalar_one() or 0
