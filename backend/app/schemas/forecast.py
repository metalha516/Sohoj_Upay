"""Pydantic V2 schemas for expense and savings forecasting."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AssumptionsSchema(BaseModel):
    """Transparent calculation and projection parameters."""

    model_config = ConfigDict(extra="allow")

    rate_type: str = "assumed"
    annual_rate: Decimal = Decimal("0.00")
    compounding_per_year: int = 12
    contribution_timing: str = "end"
    inflation_adjusted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExpenseForecastResponse(BaseModel):
    """Next-month expense forecast output with uncertainty bounds."""

    model_config = ConfigDict(from_attributes=True)

    predicted_expense: Decimal = Field(..., description="Median (p50) point forecast in BDT")
    lower_bound: Decimal = Field(..., description="10th percentile lower bound in BDT")
    upper_bound: Decimal = Field(..., description="90th percentile upper bound in BDT")
    prediction_interval_width: Decimal
    horizon_month: str = Field(..., description="Target forecast month (YYYY-MM)")
    confidence: Decimal = Field(..., description="Forecast confidence score [0.0 - 1.0]")
    model_version: str
    fallback_used: bool = False
    factors: list[dict[str, Any]] = Field(default_factory=list)
    explanation: dict[str, Any] = Field(default_factory=dict)
    assumptions: dict[str, Any] = Field(default_factory=dict)
    disclaimer_code: str = "PROJECTION_NOT_GUARANTEED"

    @property
    def point_estimate(self) -> Decimal:
        return self.predicted_expense

    @property
    def lower_bound_p10(self) -> Decimal:
        return self.lower_bound

    @property
    def upper_bound_p90(self) -> Decimal:
        return self.upper_bound


class SavingsForecastResponse(BaseModel):
    """Next-month savings forecast derived from income and expense models."""

    model_config = ConfigDict(from_attributes=True)

    projected_income: Decimal = Field(..., description="Expected monthly income in BDT")
    predicted_savings: Decimal = Field(..., description="Expected monthly savings in BDT")
    lower_bound: Decimal = Field(..., description="Conservative lower savings bound in BDT")
    upper_bound: Decimal = Field(..., description="Optimistic upper savings bound in BDT")
    savings_rate_projected: Decimal | None = Field(
        None, description="Expected savings rate percentage"
    )
    horizon_month: str = Field(..., description="Target forecast month (YYYY-MM)")
    confidence: Decimal = Field(..., description="Forecast confidence score [0.0 - 1.0]")
    model_version: str
    fallback_used: bool = False
    factors: list[dict[str, Any]] = Field(default_factory=list)
    assumptions: dict[str, Any] = Field(default_factory=dict)
    disclaimer_code: str = "PROJECTION_NOT_GUARANTEED"
