"""Repository for monthly financial features management."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feature import MonthlyFeature
from app.repositories.base import BaseRepository


class FeatureRepository(BaseRepository[MonthlyFeature]):
    """Repository for querying and updating MonthlyFeature facts."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(MonthlyFeature, session)

    async def get_by_user_and_month(self, user_id: uuid.UUID, month: date) -> MonthlyFeature | None:
        """Fetch monthly feature row for a specific user and month."""
        query = select(MonthlyFeature).where(
            MonthlyFeature.user_id == user_id,
            MonthlyFeature.month == month,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_recent_for_user(
        self, user_id: uuid.UUID, limit: int = 12
    ) -> Sequence[MonthlyFeature]:
        """Fetch recent monthly features for a user in chronological order."""
        query = (
            select(MonthlyFeature)
            .where(MonthlyFeature.user_id == user_id)
            .order_by(MonthlyFeature.month.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        rows = list(result.scalars().all())
        rows.reverse()  # Return in chronological order (earliest to latest)
        return rows

    async def upsert_feature(
        self,
        user_id: uuid.UUID,
        month: date,
        data: dict[str, Any],
    ) -> MonthlyFeature:
        """Upsert a monthly features row from calculated metrics."""
        existing = await self.get_by_user_and_month(user_id, month)
        if not existing:
            existing = MonthlyFeature(user_id=user_id, month=month)
            self.session.add(existing)

        # Update fields
        for field in (
            "income",
            "expense",
            "savings",
            "savings_rate",
            "necessity_expense",
            "discretionary_expense",
            "necessity_rate",
            "discretionary_rate",
            "txn_count",
            "cashout_count",
            "avg_txn",
            "median_txn",
            "expense_variance",
            "spending_growth",
            "income_expense_ratio",
            "savings_consistency",
            "category_breakdown",
            "computed_at",
        ):
            if field in data:
                val = data[field]
                if isinstance(val, (int, float)) and field in (
                    "income",
                    "expense",
                    "savings",
                    "necessity_expense",
                    "discretionary_expense",
                    "avg_txn",
                    "median_txn",
                ):
                    val = Decimal(str(val))
                setattr(existing, field, val)

        await self.session.flush()
        return existing
