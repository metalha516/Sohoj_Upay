"""Repository for behavioral profile persistence and queries."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.behavior import BehaviorProfile
from app.repositories.base import BaseRepository


class BehaviorRepository(BaseRepository[BehaviorProfile]):
    """Data access layer for user behavior profiles."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(BehaviorProfile, session)

    async def get_latest_profile_for_user(self, user_id: uuid.UUID) -> BehaviorProfile | None:
        """Fetch the most recently computed behavior profile for a user."""
        stmt = (
            select(BehaviorProfile)
            .where(BehaviorProfile.user_id == user_id)
            .order_by(BehaviorProfile.created_at.desc())
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_profile(
        self,
        user_id: uuid.UUID,
        profile: str,
        confidence: Decimal,
        top_factors: dict[str, Any] | list[dict[str, Any]],
        model_version: str,
        as_of_month: date,
        savings_rate: Decimal | None = None,
        necessity_rate: Decimal | None = None,
        discretionary_rate: Decimal | None = None,
        cashout_frequency: Decimal | None = None,
        spending_variance: Decimal | None = None,
    ) -> BehaviorProfile:
        """Persist a newly computed behavioral profile."""
        factors_dict = {"items": top_factors} if isinstance(top_factors, list) else top_factors
        entity = BehaviorProfile(
            user_id=user_id,
            profile=profile,
            confidence=confidence,
            top_factors=factors_dict,
            model_version=model_version,
            as_of_month=as_of_month,
            savings_rate=savings_rate,
            necessity_rate=necessity_rate,
            discretionary_rate=discretionary_rate,
            cashout_frequency=cashout_frequency,
            spending_variance=spending_variance,
        )
        return await self.create(entity)
