"""Database persistence service for ML model outputs.

Persists model inference results into behavior_profiles, anomalies,
and predictions tables with model_version provenance.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from ml.models.anomaly_detector import AnomalyOutputContract
from ml.models.behavior_classifier import BehaviorPrediction
from ml.models.expense_forecaster import ForecastOutputContract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anomaly import Anomaly
from app.models.behavior import BehaviorProfile
from app.models.prediction import Prediction


class MLPersistenceService:
    """Service to persist model outputs to database tables."""

    @staticmethod
    def create_behavior_profile_record(
        user_id: uuid.UUID,
        prediction: BehaviorPrediction,
        as_of_month: date,
        model_version: str = "v1.0.0",
        savings_rate: float | Decimal | None = None,
        necessity_rate: float | Decimal | None = None,
        discretionary_rate: float | Decimal | None = None,
        cashout_frequency: float | Decimal | None = None,
        spending_variance: float | Decimal | None = None,
    ) -> BehaviorProfile:
        """Create declarative BehaviorProfile entity."""
        return BehaviorProfile(
            user_id=user_id,
            profile=prediction.profile,
            confidence=Decimal(str(round(prediction.confidence, 4))),
            top_factors={"factors": prediction.top_factors},
            savings_rate=Decimal(str(round(float(savings_rate), 4)))
            if savings_rate is not None
            else None,
            necessity_rate=Decimal(str(round(float(necessity_rate), 4)))
            if necessity_rate is not None
            else None,
            discretionary_rate=(
                Decimal(str(round(float(discretionary_rate), 4)))
                if discretionary_rate is not None
                else None
            ),
            cashout_frequency=(
                Decimal(str(round(float(cashout_frequency), 4)))
                if cashout_frequency is not None
                else None
            ),
            spending_variance=(
                Decimal(str(round(float(spending_variance), 4)))
                if spending_variance is not None
                else None
            ),
            model_version=model_version,
            as_of_month=as_of_month,
        )

    @staticmethod
    def create_anomaly_record(
        user_id: uuid.UUID,
        anomaly_output: AnomalyOutputContract,
        transaction_id: uuid.UUID | None = None,
        model_version: str = "v1.0.0",
    ) -> Anomaly:
        """Create declarative Anomaly entity."""
        return Anomaly(
            user_id=user_id,
            transaction_id=transaction_id,
            scope=anomaly_output.scope,
            category=anomaly_output.category,
            anomaly_score=Decimal(str(round(anomaly_output.anomaly_score, 4))),
            observed_value=Decimal(str(round(anomaly_output.observed, 2))),
            baseline_value=Decimal(str(round(anomaly_output.baseline, 2))),
            deviation_pct=Decimal(str(round(anomaly_output.deviation_pct, 2))),
            explanation=anomaly_output.explanation,
            model_version=model_version,
            status="open",
        )

    @staticmethod
    def create_expense_forecast_record(
        user_id: uuid.UUID,
        forecast_output: ForecastOutputContract,
        horizon_month: date | None = None,
        model_version: str = "v1.0.0",
    ) -> Prediction:
        """Create declarative Prediction entity for next-month expense forecast."""
        val_dict = {
            "predicted_expense": forecast_output.predicted_expense,
            "lower_bound_p10": forecast_output.lower_bound_p10,
            "upper_bound_p90": forecast_output.upper_bound_p90,
            "prediction_interval_width": forecast_output.prediction_interval_width,
            "fallback_used": forecast_output.fallback_used,
            "target_month": forecast_output.target_month,
            "factors": forecast_output.factors,
        }
        return Prediction(
            user_id=user_id,
            prediction_type="expense_forecast",
            prediction_value=val_dict,
            confidence=Decimal("0.8000"),  # 80% nominal coverage
            horizon_month=horizon_month,
            model_version=model_version,
        )

    @classmethod
    async def persist_expense_forecast(
        cls,
        session: AsyncSession,
        user_id: uuid.UUID,
        forecast_output: ForecastOutputContract,
        horizon_month: date | None = None,
        model_version: str = "v1.0.0",
    ) -> Prediction:
        """Persist forecast prediction to database."""
        rec = cls.create_expense_forecast_record(
            user_id=user_id,
            forecast_output=forecast_output,
            horizon_month=horizon_month,
            model_version=model_version,
        )
        session.add(rec)
        await session.flush()
        return rec
