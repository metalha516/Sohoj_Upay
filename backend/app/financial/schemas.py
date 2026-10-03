"""Typed dataclasses for financial engine calculations and assumption transparency.

Pure Python, zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Literal

RateType = Literal["assumed", "historical", "contractual"]


@dataclass(frozen=True)
class AssumptionsBlock:
    """Explicit declaration of calculation assumptions and parameters."""

    rate_type: RateType
    annual_rate: Decimal
    compounding_per_year: int = 12
    contribution_timing: str = "end"
    inflation_adjusted: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class YearlyPoint:
    """Yearly projection step for charting and tabular inspection."""

    year: int
    balance: Decimal
    contributions: Decimal
    growth: Decimal


@dataclass(frozen=True)
class FVResult:
    """Result of future value calculation with series breakdown."""

    future_value: Decimal
    total_contributed: Decimal
    total_growth: Decimal
    assumptions: AssumptionsBlock
    series: list[YearlyPoint]
    disclaimer_code: str = "PROJECTION_NOT_GUARANTEED"


@dataclass(frozen=True)
class DoublingResult:
    """Result of investment doubling time calculation."""

    years: Decimal
    months: int
    annual_rate: Decimal
    compounding_per_year: int
    rule_of_72_approx: Decimal
    assumptions: AssumptionsBlock
    disclaimer_code: str = "PROJECTION_NOT_GUARANTEED"


@dataclass(frozen=True)
class RequiredSavingResult:
    """Result of required monthly savings calculation to hit a financial target."""

    required_monthly_saving: Decimal
    target_amount: Decimal
    current_amount: Decimal
    shortfall: Decimal
    months: int
    total_contributed: Decimal
    projected_growth: Decimal
    assumptions: AssumptionsBlock
    disclaimer_code: str = "PROJECTION_NOT_GUARANTEED"


@dataclass(frozen=True)
class GoalProgressResult:
    """Progress and feasibility assessment of an active financial goal."""

    target_amount: Decimal
    current_amount: Decimal
    shortfall: Decimal
    progress_pct: Decimal
    months_remaining: int
    is_on_track: bool
    projected_completion_date: date | None
    required_monthly_saving: Decimal
    current_monthly_saving: Decimal | None
    feasibility_status: Literal["on_track", "at_risk", "behind", "completed"]
    disclaimer_code: str = "PROJECTION_NOT_GUARANTEED"


# Alias matching design.md naming
GoalProgress = GoalProgressResult


@dataclass(frozen=True)
class EmergencyFundResult:
    """Evaluation of liquid emergency reserve coverage."""

    current_fund: Decimal
    target_fund: Decimal
    avg_monthly_essentials: Decimal
    months_target: Decimal
    months_covered: Decimal
    shortfall: Decimal
    status: Literal["critical", "vulnerable", "adequate", "optimal"]
    recommendation: str


@dataclass(frozen=True)
class AffordabilityResult:
    """Assessment of discretionary purchase affordability against cash reserves and goals."""

    is_affordable: bool
    verdict: Literal[
        "affordable_from_cash", "affordable_with_monthly_budget", "unaffordable_cash_deficit"
    ]
    purchase_amount: Decimal
    current_balance: Decimal
    upcoming_commitments: Decimal
    goals_allocation: Decimal
    available_liquidity: Decimal
    remaining_buffer: Decimal
    months_to_save_if_deferred: int | None
    explanation: str


@dataclass(frozen=True)
class ScenarioInput:
    """Baseline inputs for running financial scenarios."""

    initial_balance: Decimal
    monthly_income: Decimal
    monthly_expense: Decimal
    monthly_savings: Decimal
    annual_return_rate: Decimal = Decimal("0.00")
    horizon_years: int = 5
    rate_type: RateType = "assumed"


@dataclass(frozen=True)
class ScenarioYearPoint:
    """Year-by-year comparative trajectory."""

    year: int
    baseline_balance: Decimal
    simulated_balance: Decimal
    baseline_growth: Decimal
    simulated_growth: Decimal
    delta: Decimal


@dataclass(frozen=True)
class ScenarioResult:
    """Comparative outcome of baseline vs modified financial parameters."""

    base_future_value: Decimal
    simulated_future_value: Decimal
    net_benefit: Decimal
    assumptions: AssumptionsBlock
    yearly_comparison: list[ScenarioYearPoint]
    summary: str
    disclaimer_code: str = "PROJECTION_NOT_GUARANTEED"
