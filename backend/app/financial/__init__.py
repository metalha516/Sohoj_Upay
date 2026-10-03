"""Deterministic financial engine package.

Pure Python, exact Decimal arithmetic, zero external dependencies.
"""

from __future__ import annotations

from app.financial.engine import (
    calculate_affordability,
    calculate_doubling_time,
    calculate_emergency_fund,
    calculate_expense_ratio,
    calculate_future_value,
    calculate_goal_progress,
    calculate_monthly_required_saving,
    calculate_savings_rate,
    run_scenario,
)
from app.financial.exceptions import (
    FinancialEngineError,
    InvalidCompoundingFrequencyError,
    InvalidRateError,
    InvalidTargetDateError,
    InvalidTimingError,
    NegativeValueError,
    ZeroPeriodError,
)
from app.financial.rounding import (
    CURRENCY_PRECISION,
    RATE_PRECISION,
    RATIO_HIGH_PRECISION,
    round_currency,
    round_rate,
    round_ratio,
)
from app.financial.schemas import (
    AffordabilityResult,
    AssumptionsBlock,
    DoublingResult,
    EmergencyFundResult,
    FVResult,
    GoalProgress,
    GoalProgressResult,
    RateType,
    RequiredSavingResult,
    ScenarioInput,
    ScenarioResult,
    ScenarioYearPoint,
    YearlyPoint,
)

__all__ = [
    # Core deterministic calculation functions
    "calculate_future_value",
    "calculate_doubling_time",
    "calculate_monthly_required_saving",
    "calculate_goal_progress",
    "calculate_savings_rate",
    "calculate_expense_ratio",
    "calculate_emergency_fund",
    "calculate_affordability",
    "run_scenario",
    # Rounding helpers
    "round_currency",
    "round_rate",
    "round_ratio",
    "CURRENCY_PRECISION",
    "RATE_PRECISION",
    "RATIO_HIGH_PRECISION",
    # Data contracts & Result Schemas
    "AssumptionsBlock",
    "YearlyPoint",
    "FVResult",
    "DoublingResult",
    "RequiredSavingResult",
    "GoalProgressResult",
    "GoalProgress",
    "EmergencyFundResult",
    "AffordabilityResult",
    "ScenarioInput",
    "ScenarioYearPoint",
    "ScenarioResult",
    "RateType",
    # Strongly typed exceptions
    "FinancialEngineError",
    "NegativeValueError",
    "ZeroPeriodError",
    "InvalidRateError",
    "InvalidCompoundingFrequencyError",
    "InvalidTimingError",
    "InvalidTargetDateError",
]
