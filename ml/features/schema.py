"""Typed FeatureSchema definitions and schema versioning for Sohoj feature store."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

FEATURE_SCHEMA_VERSION = "v1.0.0"


class MonthlyFeatureRecord(BaseModel):
    """Normalized schema for user monthly financial facts and rolling window features."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    user_id: uuid.UUID
    month: date  # Normalized to YYYY-MM-01 in Asia/Dhaka
    feature_schema_version: str = Field(default=FEATURE_SCHEMA_VERSION)

    # -------------------------------------------------------------------------
    # Core Base Monthly Aggregates (design.md §4.2 monthly_features)
    # -------------------------------------------------------------------------
    income: Decimal = Field(default=Decimal("0.00"), description="Total earned inflow")
    expense: Decimal = Field(
        default=Decimal("0.00"), description="Total consumption outflows including fees"
    )
    savings: Decimal = Field(
        default=Decimal("0.00"), description="Intentional allocations to savings_goal"
    )
    savings_rate: Decimal | None = Field(
        default=None, description="savings / income (null if income <= 0)"
    )

    necessity_expense: Decimal = Field(
        default=Decimal("0.00"), description="Expenses tagged purpose=necessity"
    )
    discretionary_expense: Decimal = Field(
        default=Decimal("0.00"), description="Expenses tagged purpose=discretionary"
    )
    necessity_rate: Decimal | None = Field(default=None, description="necessity / expense")
    discretionary_rate: Decimal | None = Field(default=None, description="discretionary / expense")

    txn_count: int = Field(default=0, ge=0, description="Total transactions in month")
    cashout_count: int = Field(default=0, ge=0, description="Count of cash_out events")

    avg_txn: Decimal | None = Field(default=None, description="Mean amount across all transactions")
    median_txn: Decimal | None = Field(
        default=None, description="Median amount across all transactions"
    )
    expense_variance: Decimal | None = Field(
        default=None, description="Sample variance of expense amounts"
    )
    spending_growth: Decimal | None = Field(
        default=None, description="MoM expense growth vs previous month"
    )
    income_expense_ratio: Decimal | None = Field(default=None, description="income / expense")
    category_breakdown: dict[str, float] = Field(
        default_factory=dict, description="Category-level expenditure map"
    )

    # -------------------------------------------------------------------------
    # Rolling 3-Month Features (for Model A/B/C ML consumption)
    # -------------------------------------------------------------------------
    rolling_savings_rate_3m_mean: float | None = Field(
        default=None, description="3-month mean savings rate"
    )
    rolling_savings_rate_3m_std: float | None = Field(
        default=None, description="3-month std dev of savings rate"
    )
    savings_consistency: Decimal | None = Field(
        default=None, description="Savings consistency metric (design.md)"
    )

    rolling_expense_3m_mean: float | None = Field(
        default=None, description="3-month mean total expense"
    )
    rolling_expense_3m_std: float | None = Field(
        default=None, description="3-month std dev of expense"
    )
    spending_trend_3m: float | None = Field(
        default=None, description="Linear trend slope of expense over 3 months"
    )

    category_entropy_3m: float | None = Field(
        default=None, description="Shannon entropy of 3-month category spend"
    )
    discretionary_volatility_3m: float | None = Field(
        default=None, description="Std dev of discretionary_rate over 3 months"
    )
    deficit_months_3m: int = Field(
        default=0, ge=0, le=3, description="Count of deficit months (savings < 0 or surplus < 0)"
    )

    computed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FeatureSchemaMetadata(BaseModel):
    """Metadata describing schema contracts, column lists, and nullability."""

    version: str = FEATURE_SCHEMA_VERSION
    columns: list[str]
    rolling_window_months: int = 3
    timezone: str = "Asia/Dhaka"
    currency: str = "BDT"
