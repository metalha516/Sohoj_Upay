"""ML service orchestrating Model A (Behavior), Model B (Anomaly), and Model C (Forecast).

Features:
- Debounced profile refresh (<= 1 per N minutes per user)
- Cold-start detection with InsufficientDataError guidance
- Grounded anomaly alert generation and storage with source_refs
- Expense and savings forecasting with quantile uncertainty bounds
- Nightly batch processing for active accounts
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InsufficientDataError
from app.financial.rounding import round_currency, round_rate
from app.ml.inference import get_model_manager
from app.models.anomaly import Anomaly
from app.models.behavior import BehaviorProfile
from app.models.feature import MonthlyFeature
from app.models.user import User
from app.repositories.anomaly_repo import AnomalyRepository
from app.repositories.behavior_repo import BehaviorRepository
from app.repositories.feature_repo import FeatureRepository
from app.repositories.prediction_repo import PredictionRepository
from app.repositories.recommendation_repo import RecommendationRepository
from app.repositories.user_repo import UserRepository
from app.schemas.anomaly import AnomalyResponse
from app.schemas.behavior import (
    BehaviorInsightItem,
    BehaviorInsightsResponse,
    BehaviorProfileResponse,
)
from app.schemas.forecast import (
    ExpenseForecastResponse,
    SavingsForecastResponse,
)

logger = logging.getLogger("sohoj.ml.service")

DEBOUNCE_WINDOW_SECONDS = 900  # 15 minutes


class MLService:
    """Production service coordinating machine learning inference and insights."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.behavior_repo = BehaviorRepository(session)
        self.anomaly_repo = AnomalyRepository(session)
        self.rec_repo = RecommendationRepository(session)
        self.pred_repo = PredictionRepository(session)
        self.feature_repo = FeatureRepository(session)
        self.user_repo = UserRepository(session)
        self.model_manager = get_model_manager()

    async def get_user_behavior_profile(self, user_id: uuid.UUID) -> BehaviorProfileResponse | None:
        """Alias for get_or_refresh_behavior_profile returning None on cold start."""
        try:
            return await self.get_or_refresh_behavior_profile(user_id, allow_cold_start=True)
        except Exception:
            return None

    async def get_latest_profile(self, user_id: uuid.UUID) -> BehaviorProfileResponse | None:
        """Alias for get_user_behavior_profile."""
        return await self.get_user_behavior_profile(user_id)

    async def forecast_next_month_expense(
        self, user_id: uuid.UUID
    ) -> ExpenseForecastResponse | None:
        """Alias for get_expense_forecast."""
        try:
            return await self.get_expense_forecast(user_id)
        except Exception:
            return None

    async def get_or_refresh_behavior_profile(
        self,
        user_id: uuid.UUID,
        force: bool = False,
        allow_cold_start: bool = False,
    ) -> BehaviorProfileResponse:
        """Fetch cached profile or compute new profile with debounce enforcement."""
        # 1. Check existing profile freshness (debounce)
        latest = await self.behavior_repo.get_latest_profile_for_user(user_id)
        now = datetime.now(UTC)

        if latest and not force:
            created_at = latest.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=UTC)
            age_seconds = (now - created_at).total_seconds()
            if age_seconds < DEBOUNCE_WINDOW_SECONDS:
                return self._profile_to_schema(latest)

        # 2. Check history tenure for cold-start policy
        features = await self.feature_repo.list_recent_for_user(user_id, limit=12)
        months_active = len(features)

        if months_active < 2:
            if not allow_cold_start:
                raise InsufficientDataError(
                    detail="At least 2 months of financial history are required for behavioral classification.",
                    guidance="Continue recording transactions regularly. Behavioral archetypes unlock after 2 months of activity.",
                )
            # Cold-start profile emission
            return BehaviorProfileResponse(
                user_id=user_id,
                profile="insufficient_data",
                confidence=Decimal("0.0000"),
                top_factors=[
                    {
                        "feature": "months_active",
                        "value": months_active,
                        "direction": "low",
                        "label": f"Tenure too short ({months_active} month(s) observed, minimum 2 required)",
                    }
                ],
                savings_rate=None,
                necessity_rate=None,
                discretionary_rate=None,
                cashout_frequency=None,
                spending_variance=None,
                model_version="behavior_classifier_v1.0.0",
                as_of_month=date.today(),
                is_cold_start=True,
                created_at=now,
            )

        # 3. Ingest latest monthly feature record
        latest_feat: MonthlyFeature = features[0]
        feat_dict = self._extract_feature_dict(latest_feat)

        # 4. Run Model A
        model = self.model_manager.get_model("behavior_classifier")
        pred = model.predict(features=feat_dict, months_active=months_active)

        # 5. Persist profile
        top_factors = (
            pred.top_factors
            if hasattr(pred, "top_factors")
            else [{"feature": "general", "label": "Standard profile"}]
        )
        conf_dec = Decimal(str(round(pred.confidence, 4)))

        new_profile = await self.behavior_repo.create_profile(
            user_id=user_id,
            profile=pred.profile,
            confidence=conf_dec,
            top_factors=top_factors,
            model_version=model.model_version,
            as_of_month=latest_feat.month,
            savings_rate=latest_feat.savings_rate,
            necessity_rate=latest_feat.necessity_rate,
            discretionary_rate=latest_feat.discretionary_rate,
            cashout_frequency=Decimal(str(latest_feat.cashout_count)),
            spending_variance=latest_feat.expense_variance,
        )

        return self._profile_to_schema(new_profile)

    async def get_behavior_insights(
        self,
        user_id: uuid.UUID,
        allow_cold_start: bool = False,
    ) -> BehaviorInsightsResponse:
        """Fetch behavior archetype and personalized actionable insights."""
        profile_res = await self.get_or_refresh_behavior_profile(
            user_id, allow_cold_start=allow_cold_start
        )

        # Fetch existing recommendations from DB
        db_recs = await self.rec_repo.list_recommendations_for_user(user_id, limit=10)
        insight_items: list[BehaviorInsightItem] = [
            BehaviorInsightItem(
                id=r.id,
                type=r.type,
                title=r.title,
                content=r.content,
                priority=r.priority,
                source_refs=r.source_refs,
                created_at=r.created_at,
            )
            for r in db_recs
        ]

        # Synthesize rule-templated coaching insights if empty
        if not insight_items:
            synthesized = self._synthesize_insights(profile_res)
            for item in synthesized:
                rec_entity = await self.rec_repo.create_recommendation(
                    user_id=user_id,
                    type=item["type"],
                    title=item["title"],
                    content=item["content"],
                    priority=item["priority"],
                    source_refs=item.get("source_refs"),
                )
                insight_items.append(
                    BehaviorInsightItem(
                        id=rec_entity.id,
                        type=rec_entity.type,
                        title=rec_entity.title,
                        content=rec_entity.content,
                        priority=rec_entity.priority,
                        source_refs=rec_entity.source_refs,
                        created_at=rec_entity.created_at,
                    )
                )

        return BehaviorInsightsResponse(
            profile=profile_res.profile,
            confidence=profile_res.confidence,
            model_version=profile_res.model_version,
            top_factors=profile_res.top_factors,
            insights=insight_items,
        )

    async def get_anomalies(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        scope: str | None = None,
        limit: int = 50,
    ) -> list[AnomalyResponse]:
        """Fetch detected spending anomalies for a user."""
        items = await self.anomaly_repo.list_anomalies_for_user(
            user_id=user_id, status=status, scope=scope, limit=limit
        )
        return [self._anomaly_to_schema(a) for a in items]

    async def update_anomaly_status(
        self,
        user_id: uuid.UUID,
        anomaly_id: uuid.UUID,
        new_status: str,
    ) -> AnomalyResponse | None:
        """Update analyst / user feedback on a detected anomaly."""
        updated = await self.anomaly_repo.update_status(
            anomaly_id=anomaly_id, user_id=user_id, status=new_status
        )
        if updated is None:
            return None
        return self._anomaly_to_schema(updated)

    async def evaluate_transaction_anomaly(
        self,
        user_id: uuid.UUID,
        txn_id: uuid.UUID | None,
        amount: Decimal,
        category: str,
    ) -> Anomaly | None:
        """Run Model B on a transaction and persist anomaly and recommendation if flagged."""
        detector = self.model_manager.get_model("anomaly_detector")
        amt_float = float(amount)

        # Detect
        res = detector.predict(
            amount=amt_float,
            category=category,
            user_id=str(user_id),
        )

        if not res.is_anomaly or res.budget_suppressed:
            return None

        anomaly = await self.anomaly_repo.create_anomaly(
            user_id=user_id,
            transaction_id=txn_id,
            scope="transaction",
            category=category,
            anomaly_score=Decimal(str(round(res.anomaly_score, 4))),
            observed_value=round_currency(Decimal(str(res.observed))),
            baseline_value=round_currency(Decimal(str(res.baseline))),
            deviation_pct=round_rate(Decimal(str(res.deviation_pct))),
            explanation=res.explanation,
            model_version=detector.model_version,
            status="open",
        )

        # Create linked AI recommendation with source_refs
        await self.rec_repo.create_recommendation(
            user_id=user_id,
            type="anomaly_alert",
            title=f"Unusual spending in {category}",
            content=(
                f"We observed a transaction of ৳{amount:,.2f} in {category}, "
                f"which is {res.deviation_pct:.1f}% higher than your typical baseline of ৳{res.baseline:,.2f}."
            ),
            priority=1,
            source_refs={
                "anomaly_id": str(anomaly.id),
                "transaction_id": str(txn_id) if txn_id else None,
                "scope": "transaction",
                "category": category,
                "deviation_pct": float(res.deviation_pct),
            },
        )

        return anomaly

    async def get_expense_forecast(
        self,
        user_id: uuid.UUID,
        allow_cold_start: bool = False,
    ) -> ExpenseForecastResponse:
        """Generate next-month expense forecast with uncertainty bounds."""
        features = await self.feature_repo.list_recent_for_user(user_id, limit=6)
        months_active = len(features)

        if months_active < 2 and not allow_cold_start:
            raise InsufficientDataError(
                detail="At least 2 months of transaction history are required to forecast expenses.",
                guidance="Continue tracking your daily expenses. Next-month forecasts unlock after 2 months of activity.",
            )

        forecaster = self.model_manager.get_model("expense_forecaster")

        # Determine target month
        today = date.today()
        target_year = today.year + (1 if today.month == 12 else 0)
        target_month_num = 1 if today.month == 12 else today.month + 1
        target_month_str = f"{target_year:04d}-{target_month_num:02d}"

        # Feed lag features if available
        curr_exp = float(features[0].expense) if features else 15000.0
        lag2 = float(features[1].expense) if len(features) > 1 else curr_exp
        lag3 = float(features[2].expense) if len(features) > 2 else lag2
        rolling_mean = (
            float(np.mean([float(f.expense) for f in features[:3]])) if features else curr_exp
        )
        rolling_std = (
            float(np.std([float(f.expense) for f in features[:3]]))
            if len(features) > 1
            else (0.15 * curr_exp)
        )

        sr = float(features[0].savings_rate or 0.15) if features else 0.15
        nr = float(features[0].necessity_rate or 0.70) if features else 0.70
        dr = float(features[0].discretionary_rate or 0.15) if features else 0.15
        inc = float(features[0].income) if features else (curr_exp * 1.25)
        tx_cnt = features[0].txn_count if features else 25
        co_cnt = features[0].cashout_count if features else 2

        contract = forecaster.predict(
            current_expense=curr_exp,
            lag2_expense=lag2,
            lag3_expense=lag3,
            rolling_3m_mean=rolling_mean,
            rolling_3m_std=rolling_std,
            income=inc,
            savings_rate=sr,
            necessity_rate=nr,
            discretionary_rate=dr,
            txn_count=tx_cnt,
            cashout_count=co_cnt,
            target_month_num=target_month_num,
            target_month_str=target_month_str,
            history_months_count=months_active,
        )

        p50 = Decimal(str(round(contract.predicted_expense, 2)))
        p10 = Decimal(str(round(contract.lower_bound_p10, 2)))
        p90 = Decimal(str(round(contract.upper_bound_p90, 2)))
        width = Decimal(str(round(contract.prediction_interval_width, 2)))
        confidence = Decimal("0.8500") if not contract.fallback_used else Decimal("0.6500")

        assumptions = {
            "method": "quantile_lightgbm"
            if not contract.fallback_used
            else "3m_moving_average_fallback",
            "quantiles": [0.10, 0.50, 0.90],
            "target_horizon": "1_month",
            "historical_months_used": months_active,
        }

        # Persist prediction
        target_horizon_date = date(target_year, target_month_num, 1)
        await self.pred_repo.create_prediction(
            user_id=user_id,
            prediction_type="expense_forecast",
            prediction_value={
                "predicted_expense": str(p50),
                "lower_bound": str(p10),
                "upper_bound": str(p90),
            },
            confidence=confidence,
            horizon_month=target_horizon_date,
            model_version=forecaster.model_version,
        )

        return ExpenseForecastResponse(
            predicted_expense=p50,
            lower_bound=p10,
            upper_bound=p90,
            prediction_interval_width=width,
            horizon_month=target_month_str,
            confidence=confidence,
            model_version=forecaster.model_version,
            fallback_used=contract.fallback_used,
            factors=contract.factors,
            explanation=contract.explanation,
            assumptions=assumptions,
            disclaimer_code="PROJECTION_NOT_GUARANTEED",
        )

    async def get_savings_forecast(
        self,
        user_id: uuid.UUID,
        allow_cold_start: bool = False,
    ) -> SavingsForecastResponse:
        """Derive next-month savings forecast from income and expense projections."""
        features = await self.feature_repo.list_recent_for_user(user_id, limit=6)
        months_active = len(features)

        if months_active < 2 and not allow_cold_start:
            raise InsufficientDataError(
                detail="At least 2 months of transaction history are required to forecast savings.",
                guidance="Continue recording transactions to establish a reliable baseline for savings projections.",
            )

        # 1. Get expense forecast
        exp_res = await self.get_expense_forecast(user_id, allow_cold_start=allow_cold_start)

        # 2. Estimate income
        user = await self.user_repo.get_by_id(user_id)
        if features and features[0].income > Decimal("0.00"):
            proj_income = round_currency(
                Decimal(str(np.mean([float(f.income) for f in features[:3]])))
            )
        elif user and user.monthly_income:
            proj_income = user.monthly_income
        else:
            proj_income = round_currency(exp_res.predicted_expense * Decimal("1.25"))

        # 3. Calculate projected savings bounds
        pred_savings = round_currency(max(Decimal("0.00"), proj_income - exp_res.predicted_expense))
        lower_savings = round_currency(max(Decimal("0.00"), proj_income - exp_res.upper_bound))
        upper_savings = round_currency(max(Decimal("0.00"), proj_income - exp_res.lower_bound))

        sr_proj = (
            round_rate((pred_savings / proj_income) * Decimal("100.00"))
            if proj_income > Decimal("0.00")
            else None
        )

        factors = [
            {
                "name": "Projected Income Baseline",
                "value": f"৳{proj_income:,.2f}",
                "impact": "Primary driver of total cash available for savings",
            },
            {
                "name": "Projected Expenses (p50)",
                "value": f"৳{exp_res.predicted_expense:,.2f}",
                "impact": "Directly impacts surplus allocation",
            },
        ]

        assumptions = {
            "method": "income_less_expense_quantile",
            "income_basis": "3m_historical_average",
            "expense_basis": exp_res.assumptions.get("method", "quantile_lightgbm"),
            "target_horizon": "1_month",
        }

        # Persist prediction
        horizon_parts = exp_res.horizon_month.split("-")
        target_horizon_date = date(int(horizon_parts[0]), int(horizon_parts[1]), 1)
        await self.pred_repo.create_prediction(
            user_id=user_id,
            prediction_type="savings_forecast",
            prediction_value={
                "projected_income": str(proj_income),
                "predicted_savings": str(pred_savings),
                "lower_bound": str(lower_savings),
                "upper_bound": str(upper_savings),
            },
            confidence=exp_res.confidence,
            horizon_month=target_horizon_date,
            model_version=exp_res.model_version,
        )

        return SavingsForecastResponse(
            projected_income=proj_income,
            predicted_savings=pred_savings,
            lower_bound=lower_savings,
            upper_bound=upper_savings,
            savings_rate_projected=sr_proj,
            horizon_month=exp_res.horizon_month,
            confidence=exp_res.confidence,
            model_version=exp_res.model_version,
            fallback_used=exp_res.fallback_used,
            factors=factors,
            assumptions=assumptions,
            disclaimer_code="PROJECTION_NOT_GUARANTEED",
        )

    async def run_nightly_batch_job(self) -> dict[str, int]:
        """Execute scheduled batch refresh for all active users."""
        stmt = select(User)
        users_res = await self.session.execute(stmt)
        users = list(users_res.scalars().all())

        stats = {
            "users_processed": 0,
            "profiles_updated": 0,
            "forecasts_generated": 0,
            "errors": 0,
        }

        for user in users:
            stats["users_processed"] += 1
            try:
                # 1. Update behavior profile
                await self.get_or_refresh_behavior_profile(
                    user.id, force=True, allow_cold_start=True
                )
                stats["profiles_updated"] += 1

                # 2. Generate forecasts
                await self.get_expense_forecast(user.id, allow_cold_start=True)
                await self.get_savings_forecast(user.id, allow_cold_start=True)
                stats["forecasts_generated"] += 2
            except Exception as e:
                logger.error("Nightly batch failure for user %s: %s", user.id, e)
                stats["errors"] += 1

        await self.session.commit()
        return stats

    def _extract_feature_dict(self, feat: MonthlyFeature) -> dict[str, Any]:
        """Convert MonthlyFeature entity to dimensionless classifier input dict."""
        sr = float(feat.savings_rate) if feat.savings_rate is not None else 0.15
        nr = float(feat.necessity_rate) if feat.necessity_rate is not None else 0.70
        dr = float(feat.discretionary_rate) if feat.discretionary_rate is not None else 0.15
        co_cnt = float(feat.cashout_count)
        tx_cnt = float(feat.txn_count)
        co_ratio = co_cnt / max(1.0, tx_cnt)
        exp_float = float(feat.expense)
        var_float = float(feat.expense_variance or 0.0)
        vol_cv = np.sqrt(var_float) / max(1.0, exp_float) if var_float > 0 else 0.10

        return {
            "savings_rate": sr,
            "necessity_rate": nr,
            "discretionary_rate": dr,
            "cashout_ratio": co_ratio,
            "cashout_count": co_cnt,
            "txn_count": tx_cnt,
            "volatility_cv": vol_cv,
            "expense": exp_float,
            "income": float(feat.income),
        }

    def _profile_to_schema(self, entity: BehaviorProfile) -> BehaviorProfileResponse:
        """Map ORM entity to response schema."""
        top_factors_val = (
            entity.top_factors.get("items", entity.top_factors)
            if isinstance(entity.top_factors, dict)
            else entity.top_factors
        )
        created_at = entity.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)

        return BehaviorProfileResponse(
            user_id=entity.user_id,
            profile=entity.profile,
            confidence=entity.confidence,
            top_factors=top_factors_val,
            savings_rate=entity.savings_rate,
            necessity_rate=entity.necessity_rate,
            discretionary_rate=entity.discretionary_rate,
            cashout_frequency=entity.cashout_frequency,
            spending_variance=entity.spending_variance,
            model_version=entity.model_version,
            as_of_month=entity.as_of_month,
            is_cold_start=(entity.profile == "insufficient_data"),
            created_at=created_at,
        )

    def _anomaly_to_schema(self, entity: Anomaly) -> AnomalyResponse:
        """Map ORM anomaly entity to response schema."""
        created_at = entity.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)

        return AnomalyResponse(
            id=entity.id,
            transaction_id=entity.transaction_id,
            scope=entity.scope,
            category=entity.category,
            anomaly_score=entity.anomaly_score,
            confidence=entity.anomaly_score,
            observed_value=entity.observed_value,
            baseline_value=entity.baseline_value,
            deviation_pct=entity.deviation_pct,
            explanation=entity.explanation,
            model_version=entity.model_version,
            status=entity.status,
            created_at=created_at,
        )

    def _synthesize_insights(self, profile: BehaviorProfileResponse) -> list[dict[str, Any]]:
        """Synthesize initial grounded rule insights from user behavior profile."""
        items: list[dict[str, Any]] = []

        if profile.is_cold_start:
            items.append(
                {
                    "type": "onboarding_tip",
                    "title": "Build your financial baseline",
                    "content": "Keep tracking your daily spending. After 2 months of records, personalized archetype insights and forecasts will unlock automatically.",
                    "priority": 2,
                    "source_refs": {"stage": "cold_start"},
                }
            )
            return items

        # Tailored to archetype
        if profile.profile == "disciplined_saver":
            items.append(
                {
                    "type": "growth_tip",
                    "title": "Optimize your surplus capital",
                    "content": "You consistently maintain a healthy savings buffer. Exploring formal banking DPS schemes or fixed deposits can help beat inflation.",
                    "priority": 3,
                    "source_refs": {"archetype": profile.profile},
                }
            )
        elif profile.profile == "paycheck_to_paycheck":
            items.append(
                {
                    "type": "buffer_tip",
                    "title": "Build an essential safety cushion",
                    "content": "Most cash leaves your wallet within days of receipt. Setting aside a small micro-saving (৳50-100) right after cash-in creates breathing room.",
                    "priority": 1,
                    "source_refs": {"archetype": profile.profile},
                }
            )
        else:
            items.append(
                {
                    "type": "general_coaching",
                    "title": "Maintain positive financial momentum",
                    "content": "Review your weekly necessity expenditures against your income schedule to sustain healthy cashflow balance.",
                    "priority": 3,
                    "source_refs": {"archetype": profile.profile},
                }
            )

        return items
