"""Repository for financial anomaly detection records and analyst feedback."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anomaly import Anomaly
from app.repositories.base import BaseRepository


class AnomalyRepository(BaseRepository[Anomaly]):
    """Data access layer for detected transaction and category spending anomalies."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Anomaly, session)

    async def create_anomaly(
        self,
        user_id: uuid.UUID,
        transaction_id: uuid.UUID | None,
        scope: str,
        category: str | None,
        anomaly_score: Decimal,
        observed_value: Decimal,
        baseline_value: Decimal,
        deviation_pct: Decimal,
        explanation: dict[str, Any],
        model_version: str,
        status: str = "open",
    ) -> Anomaly:
        """Record a newly detected spending anomaly."""
        anomaly = Anomaly(
            user_id=user_id,
            transaction_id=transaction_id,
            scope=scope,
            category=category,
            anomaly_score=anomaly_score,
            observed_value=observed_value,
            baseline_value=baseline_value,
            deviation_pct=deviation_pct,
            explanation=explanation,
            model_version=model_version,
            status=status,
        )
        return await self.create(anomaly)

    async def list_anomalies_for_user(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        scope: str | None = None,
        limit: int = 50,
    ) -> list[Anomaly]:
        """Fetch anomalies for a user with optional status and scope filters."""
        stmt = (
            select(Anomaly)
            .where(Anomaly.user_id == user_id)
            .order_by(Anomaly.created_at.desc())
            .limit(limit)
        )
        if status:
            stmt = stmt.where(Anomaly.status == status)
        if scope:
            stmt = stmt.where(Anomaly.scope == scope)

        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_by_id_for_user(self, entity_id: uuid.UUID, user_id: uuid.UUID) -> Anomaly | None:
        """Fetch a specific anomaly ensuring tenant ownership."""
        stmt = select(Anomaly).where(
            Anomaly.id == entity_id,
            Anomaly.user_id == user_id,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update_status(
        self, anomaly_id: uuid.UUID, user_id: uuid.UUID, status: str
    ) -> Anomaly | None:
        """Update anomaly feedback status (e.g. 'dismissed', 'confirmed')."""
        anomaly = await self.get_by_id_for_user(anomaly_id, user_id)
        if anomaly is None:
            return None
        anomaly.status = status
        await self.session.flush()
        await self.session.refresh(anomaly)
        return anomaly
