"""Repository for grounded AI and rule recommendations."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import AIRecommendation
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[AIRecommendation]):
    """Data access layer for personalized financial recommendations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AIRecommendation, session)

    async def create_recommendation(
        self,
        user_id: uuid.UUID,
        type: str,
        title: str,
        content: str,
        priority: int = 3,
        source_refs: dict[str, Any] | None = None,
    ) -> AIRecommendation:
        """Create a new grounded financial recommendation."""
        rec = AIRecommendation(
            user_id=user_id,
            type=type,
            title=title,
            content=content,
            priority=priority,
            source_refs=source_refs,
        )
        return await self.create(rec)

    async def list_recommendations_for_user(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> list[AIRecommendation]:
        """Fetch prioritized recommendations for a user."""
        stmt = (
            select(AIRecommendation)
            .where(AIRecommendation.user_id == user_id)
            .order_by(AIRecommendation.priority.asc(), AIRecommendation.created_at.desc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
