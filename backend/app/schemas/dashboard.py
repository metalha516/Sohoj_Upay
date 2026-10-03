"""Pydantic V2 schemas for user dashboard, monthly time series, and category breakdown."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DashboardSummaryResponse(BaseModel):
    """Real-time financial health summary aggregated from monthly features and active goals."""

    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    month: date
    income: Decimal = Decimal("0.00")
    expense: Decimal = Decimal("0.00")
    savings: Decimal = Decimal("0.00")
    savings_rate: Decimal | None = None
    emergency_fund_tier: str = "vulnerable"
    emergency_fund_months: Decimal = Decimal("0.00")
    active_goals_count: int = 0
    total_target_amount: Decimal = Decimal("0.00")
    total_saved_amount: Decimal = Decimal("0.00")
    average_goal_progress_pct: Decimal = Decimal("0.00")

    @property
    def unallocated_surplus(self) -> Decimal:
        return max(Decimal("0.00"), self.income - self.expense - self.savings)


class MonthlyFeatureItem(BaseModel):
    """Historical monthly feature data point for charts."""

    model_config = ConfigDict(from_attributes=True)

    month: date
    income: Decimal
    expense: Decimal
    savings: Decimal
    savings_rate: Decimal | None = None
    necessity_expense: Decimal
    discretionary_expense: Decimal
    txn_count: int
    cashout_count: int

    @property
    def necessity_rate(self) -> Decimal | None:
        return self.necessity_expense / self.expense if self.expense > Decimal("0.00") else None

    @property
    def discretionary_rate(self) -> Decimal | None:
        return self.discretionary_expense / self.expense if self.expense > Decimal("0.00") else None


class DashboardMonthlyResponse(BaseModel):
    """Time-series of monthly features for multi-month financial visualizations."""

    months: list[MonthlyFeatureItem]


class DashboardCategoryItem(BaseModel):
    """Category spending breakdown item."""

    category: str
    amount: Decimal
    percentage: Decimal
    purpose: str | None = None


class DashboardCategoriesResponse(BaseModel):
    """Monthly category composition and necessity vs. discretionary ratio."""

    month: date
    total_expense: Decimal
    necessity_expense: Decimal
    discretionary_expense: Decimal
    categories: list[DashboardCategoryItem]
