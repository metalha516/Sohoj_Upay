"""Dashboard aggregation service with multi-tier caching per security.md §3."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_manager
from app.financial.engine import calculate_emergency_fund
from app.financial.rounding import round_currency, round_ratio
from app.repositories.feature_repo import FeatureRepository
from app.repositories.goal_repo import GoalRepository
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.user_repo import UserRepository
from app.schemas.dashboard import (
    DashboardCategoriesResponse,
    DashboardCategoryItem,
    DashboardMonthlyResponse,
    DashboardSummaryResponse,
    MonthlyFeatureItem,
)


class DashboardService:
    """Aggregates pre-computed monthly features and goals into high-performance cached dashboard cards."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.feature_repo = FeatureRepository(session)
        self.goal_repo = GoalRepository(session)
        self.txn_repo = TransactionRepository(session)
        self.user_repo = UserRepository(session)

    async def get_summary(self, user_id: uuid.UUID) -> DashboardSummaryResponse:
        """Fetch primary dashboard summary card, cached for <= 60 seconds."""
        cache_key = f"dashboard:{user_id}:summary"
        cached = await cache_manager.get(cache_key)
        if cached:
            return DashboardSummaryResponse.model_validate(cached)

        now = datetime.now(UTC)
        current_month = date(now.year, now.month, 1)

        feature = await self.feature_repo.get_by_user_and_month(user_id, current_month)
        if not feature:
            recent = await self.feature_repo.list_recent_for_user(user_id, limit=1)
            feature = recent[0] if recent else None

        income = feature.income if feature else Decimal("0.00")
        expense = feature.expense if feature else Decimal("0.00")
        # savings = income - expense is the correct net savings for the month.
        # The feature engine only sets savings for savings_goal transactions,
        # so we always derive it as income - expense.
        raw_savings = feature.savings if feature else Decimal("0.00")
        savings = (income - expense) if (raw_savings == Decimal("0.00") and income > Decimal("0.00")) else raw_savings
        savings_rate = (
            feature.savings_rate
            if feature and feature.savings_rate is not None
            else (round(float(savings / income), 4) if income > Decimal("0.00") else None)
        )

        # Emergency fund tier
        user = await self.user_repo.get_by_id(user_id)
        user_inc = (
            user.monthly_income if user and user.monthly_income is not None else Decimal("0.00")
        )
        liquid_savings: Decimal = savings if savings > Decimal("0.00") else user_inc
        essential_expense = (
            feature.necessity_expense
            if feature and feature.necessity_expense > Decimal("0.00")
            else (expense if expense > Decimal("0.00") else Decimal("5000.00"))
        )

        try:
            ef_res = calculate_emergency_fund(
                avg_monthly_essentials=essential_expense,
                current_fund=liquid_savings,
            )
            ef_tier = ef_res.status
            ef_months = ef_res.months_covered
        except Exception:
            ef_tier = "vulnerable"
            ef_months = Decimal("0.00")

        # Goals metrics
        active_goals = await self.goal_repo.list_active_for_user(user_id)
        goals_count = len(active_goals)
        total_target = sum((g.target_amount for g in active_goals), Decimal("0.00"))
        total_saved = sum((g.current_amount for g in active_goals), Decimal("0.00"))
        avg_progress = (
            round_ratio(total_saved / total_target)
            if total_target > Decimal("0.00")
            else Decimal("0.00")
        )

        summary = DashboardSummaryResponse(
            user_id=user_id,
            month=current_month,
            income=income,
            expense=expense,
            savings=savings,
            savings_rate=savings_rate,
            emergency_fund_tier=ef_tier,
            emergency_fund_months=ef_months,
            active_goals_count=goals_count,
            total_target_amount=total_target,
            total_saved_amount=total_saved,
            average_goal_progress_pct=avg_progress,
        )

        await cache_manager.set(cache_key, summary.model_dump(mode="json"), ttl=60)
        return summary

    async def get_dashboard_summary(self, user_id: uuid.UUID) -> DashboardSummaryResponse:
        """Alias for get_summary."""
        return await self.get_summary(user_id)

    async def get_monthly_features(
        self, user_id: uuid.UUID, months: int = 12
    ) -> list[MonthlyFeatureItem]:
        """Fetch chronological list of monthly feature items."""
        resp = await self.get_monthly_history(user_id=user_id, limit=months)
        return resp.months

    async def get_monthly_history(
        self, user_id: uuid.UUID, limit: int = 12
    ) -> DashboardMonthlyResponse:
        """Fetch chronological multi-month financial time series, cached for <= 60 seconds."""
        cache_key = f"dashboard:{user_id}:monthly:{limit}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return DashboardMonthlyResponse.model_validate(cached)

        features = await self.feature_repo.list_recent_for_user(user_id, limit=limit)
        items = [MonthlyFeatureItem.model_validate(f) for f in features]
        resp = DashboardMonthlyResponse(months=items)

        await cache_manager.set(cache_key, resp.model_dump(mode="json"), ttl=60)
        return resp

    async def get_categories(
        self, user_id: uuid.UUID, target_month: date | None = None
    ) -> DashboardCategoriesResponse:
        """Fetch category spending breakdown for the requested month, cached for <= 60 seconds."""
        now = datetime.now(UTC)
        m = target_month or date(now.year, now.month, 1)
        cache_key = f"dashboard:{user_id}:categories:{m}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return DashboardCategoriesResponse.model_validate(cached)

        feature = await self.feature_repo.get_by_user_and_month(user_id, m)
        category_items: list[DashboardCategoryItem] = []
        total_expense = feature.expense if feature else Decimal("0.00")
        necessity = feature.necessity_expense if feature else Decimal("0.00")
        discretionary = feature.discretionary_expense if feature else Decimal("0.00")

        if feature and feature.category_breakdown:
            for cat_name, amt_val in feature.category_breakdown.items():
                amt = Decimal(str(amt_val))
                pct = (
                    round_ratio(amt / total_expense)
                    if total_expense > Decimal("0.00")
                    else Decimal("0.00")
                )
                category_items.append(
                    DashboardCategoryItem(
                        category=cat_name,
                        amount=round_currency(amt),
                        percentage=pct,
                    )
                )

        resp = DashboardCategoriesResponse(
            month=m,
            total_expense=total_expense,
            necessity_expense=necessity,
            discretionary_expense=discretionary,
            categories=category_items,
        )

        await cache_manager.set(cache_key, resp.model_dump(mode="json"), ttl=60)
        return resp
