"""Pydantic V2 schemas for deterministic financial engine simulations."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class YearlyPointSchema(BaseModel):
    """Yearly projection step."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    balance: Decimal
    contributions: Decimal
    growth: Decimal


class SimulateGrowthRequest(BaseModel):
    """Payload to simulate compound growth and future value."""

    model_config = ConfigDict(extra="forbid")

    initial_deposit: Annotated[Decimal, Field(ge=0, default=Decimal("0.00"))]
    monthly_contribution: Annotated[Decimal, Field(ge=0, default=Decimal("0.00"))]
    annual_rate: Annotated[Decimal, Field(ge=0, le=10, default=Decimal("0.07"))]
    years: Annotated[int, Field(gt=0, le=50, default=5)]
    compounding_per_year: Annotated[int, Field(default=12)]
    timing: Literal["end", "begin"] = "end"
    rate_type: Literal["assumed", "historical", "contractual"] = "assumed"
    inflation_adjusted: bool = False


class SimulateGrowthResponse(BaseModel):
    """Outcome of compound growth simulation."""

    model_config = ConfigDict(from_attributes=True)

    future_value: Decimal
    total_contributed: Decimal
    total_growth: Decimal
    series: list[YearlyPointSchema]
    confidence: Decimal = Decimal("1.0000")
    model_version: str = "financial_engine_v1.0.0"
    assumptions: dict[str, Any]
    disclaimer_code: str = "PROJECTION_NOT_GUARANTEED"


class SimulateGoalRequest(BaseModel):
    """Payload to simulate monthly savings required to hit a goal."""

    model_config = ConfigDict(extra="forbid")

    target_amount: Annotated[Decimal, Field(gt=0)]
    current_amount: Annotated[Decimal, Field(ge=0, default=Decimal("0.00"))]
    months: Annotated[int, Field(gt=0, le=600, default=12)]
    annual_rate: Annotated[Decimal, Field(ge=0, le=10, default=Decimal("0.00"))]
    contribution_timing: Literal["end", "begin"] = "end"
    rate_type: Literal["assumed", "historical", "contractual"] = "assumed"


class SimulateGoalResponse(BaseModel):
    """Outcome of goal required savings simulation."""

    model_config = ConfigDict(from_attributes=True)

    required_monthly_saving: Decimal
    target_amount: Decimal
    current_amount: Decimal
    shortfall: Decimal
    months: int
    total_contributed: Decimal
    projected_growth: Decimal
    confidence: Decimal = Decimal("1.0000")
    model_version: str = "financial_engine_v1.0.0"
    assumptions: dict[str, Any]
    disclaimer_code: str = "PROJECTION_NOT_GUARANTEED"


class SimulateDoublingRequest(BaseModel):
    """Payload to simulate investment doubling time (Rule of 72 & exact compound)."""

    model_config = ConfigDict(extra="forbid")

    annual_rate: Annotated[Decimal, Field(gt=0, le=10)]
    compounding_per_year: Annotated[int, Field(default=12)]
    rate_type: Literal["assumed", "historical", "contractual"] = "assumed"


class SimulateDoublingResponse(BaseModel):
    """Outcome of doubling time simulation."""

    model_config = ConfigDict(from_attributes=True)

    years: Decimal
    months: int
    annual_rate: Decimal
    rule_of_72_approx: Decimal
    compounding_per_year: int
    confidence: Decimal = Decimal("1.0000")
    model_version: str = "financial_engine_v1.0.0"
    assumptions: dict[str, Any]
    disclaimer_code: str = "PROJECTION_NOT_GUARANTEED"


class ScenarioInputSchema(BaseModel):
    """Baseline or simulated scenario parameters."""

    model_config = ConfigDict(extra="forbid")

    initial_balance: Annotated[Decimal, Field(ge=0)]
    monthly_income: Annotated[Decimal, Field(ge=0)]
    monthly_expense: Annotated[Decimal, Field(ge=0)]
    monthly_savings: Annotated[Decimal, Field(ge=0)]
    annual_return_rate: Annotated[Decimal, Field(ge=0, le=10, default=Decimal("0.00"))]
    horizon_years: Annotated[int, Field(gt=0, le=50, default=5)]
    rate_type: Literal["assumed", "historical", "contractual"] = "assumed"


class ScenarioYearPointSchema(BaseModel):
    """Yearly comparative step between baseline and simulation."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    baseline_balance: Decimal
    simulated_balance: Decimal
    baseline_growth: Decimal
    simulated_growth: Decimal
    delta: Decimal


class SimulateScenarioRequest(BaseModel):
    """Payload to compare baseline and modified scenarios."""

    model_config = ConfigDict(extra="forbid")

    baseline: ScenarioInputSchema
    simulated: ScenarioInputSchema


class SimulateScenarioResponse(BaseModel):
    """Outcome of comparative scenario simulation."""

    model_config = ConfigDict(from_attributes=True)

    base_future_value: Decimal
    simulated_future_value: Decimal
    net_benefit: Decimal
    yearly_comparison: list[ScenarioYearPointSchema]
    summary: str
    confidence: Decimal = Decimal("1.0000")
    model_version: str = "financial_engine_v1.0.0"
    assumptions: dict[str, Any]
    disclaimer_code: str = "PROJECTION_NOT_GUARANTEED"
