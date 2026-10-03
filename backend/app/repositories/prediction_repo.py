"""Repository for machine learning forecasts and simulation predictions."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction
from app.repositories.base import BaseRepository


class PredictionRepository(BaseRepository[Prediction]):
    """Data access layer for ML forecasts and projections."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Prediction, session)

    async def create_prediction(
        self,
        user_id: uuid.UUID,
        prediction_type: str,
        prediction_value: dict[str, Any],
        confidence: Decimal | None,
        horizon_month: date | None,
        model_version: str,
    ) -> Prediction:
        """Persist a newly computed forecast or prediction output."""
        prediction = Prediction(
            user_id=user_id,
            prediction_type=prediction_type,
            prediction_value=prediction_value,
            confidence=confidence,
            horizon_month=horizon_month,
            model_version=model_version,
        )
        return await self.create(prediction)

    async def get_latest_for_user(
        self, user_id: uuid.UUID, prediction_type: str
    ) -> Prediction | None:
        """Fetch the latest forecast of a given type for a user."""
        stmt = (
            select(Prediction)
            .where(
                Prediction.user_id == user_id,
                Prediction.prediction_type == prediction_type,
            )
            .order_by(Prediction.created_at.desc())
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
