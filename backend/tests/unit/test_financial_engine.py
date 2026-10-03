"""Comprehensive unit, golden fixture, boundary, and property tests for the financial engine.

Tests:
1. AST Import Boundary: Asserts zero dependencies on DB, ORM, ML, AI, FastAPI, or SQLAlchemy.
2. Golden Fixtures: Validated against independent closed-form spreadsheet/finance formulas.
3. Edge Cases & Typed Exceptions: Negative values, zero periods, rate limits, invalid frequencies.
4. Property-Based Testing (Hypothesis): Monotonicity, non-negativity, lower bounds, doubling identity.
"""

from __future__ import annotations

import ast
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.financial import (
    FinancialEngineError,
    InvalidCompoundingFrequencyError,
    InvalidRateError,
    InvalidTargetDateError,
    InvalidTimingError,
    NegativeValueError,
    ScenarioInput,
    ZeroPeriodError,
    calculate_affordability,
    calculate_doubling_time,
    calculate_emergency_fund,
    calculate_expense_ratio,
    calculate_future_value,
    calculate_goal_progress,
    calculate_monthly_required_saving,
    calculate_savings_rate,
    round_currency,
    round_rate,
    round_ratio,
    run_scenario,
)

# -----------------------------------------------------------------------------
# 1. AST Import Boundary Test
# -----------------------------------------------------------------------------


def test_ast_import_boundary() -> None:
    """Enforce strict architectural isolation: app.financial must have ZERO external dependencies."""
    financial_dir = Path(__file__).resolve().parent.parent.parent / "app" / "financial"
    assert financial_dir.exists(), f"Financial directory not found at {financial_dir}"

    forbidden_modules = {
        "sqlalchemy",
        "fastapi",
        "starlette",
        "pydantic",
        "app.models",
        "app.db",
        "app.ml",
        "app.services",
        "app.api",
        "ml",
        "torch",
        "sklearn",
        "lightgbm",
        "xgboost",
        "joblib",
    }

    for py_file in financial_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for forbidden in forbidden_modules:
                        assert not alias.name.startswith(forbidden), (
                            f"Illegal import '{alias.name}' in {py_file.name}"
                        )
            elif isinstance(node, ast.ImportFrom) and node.module:
                for forbidden in forbidden_modules:
                    assert not node.module.startswith(forbidden), (
                        f"Illegal from-import '{node.module}' in {py_file.name}"
                    )


# -----------------------------------------------------------------------------
# 2. Golden Fixtures & Reference Implementations
# -----------------------------------------------------------------------------


def test_calculate_future_value_lump_sum_only() -> None:
    """Golden test: 10,000 BDT at 8% annual for 1 year with monthly compounding."""
    res = calculate_future_value(
        principal=Decimal("10000.00"),
        annual_rate=Decimal("0.08"),
        years=1,
        monthly_contribution=Decimal("0.00"),
        compounding_per_year=12,
        rate_type="contractual",
    )
    # 10000 * (1 + 0.08/12)^12 = 10829.995... -> 10830.00
    assert res.future_value == Decimal("10830.00")
    assert res.total_contributed == Decimal("10000.00")
    assert res.total_growth == Decimal("830.00")
    assert res.assumptions.rate_type == "contractual"
    assert len(res.series) == 1
    assert res.series[0].year == 1
    assert res.series[0].balance == Decimal("10830.00")


def test_calculate_future_value_with_contributions_end() -> None:
    """Golden test: 5,000 principal + 1,000/mo for 2 years at 6% annual (end of month)."""
    res = calculate_future_value(
        principal=Decimal("5000.00"),
        annual_rate=Decimal("0.06"),
        years=2,
        monthly_contribution=Decimal("1000.00"),
        compounding_per_year=12,
        contribution_timing="end",
        rate_type="assumed",
    )
    # Lump sum: 5000 * (1 + 0.005)^24 = 5635.7989...
    # Annuity end: 1000 * ((1.005^24 - 1)/0.005) = 25431.9552...
    # Total unrounded = 31067.754... -> 31067.75
    assert res.future_value == Decimal("31067.75")
    assert res.total_contributed == Decimal("29000.00")  # 5000 + 1000 * 24
    assert res.total_growth == Decimal("2067.75")
    assert len(res.series) == 2


def test_calculate_future_value_with_contributions_begin() -> None:
    """Golden test: Annuity due (begin of month) has factor (1 + i)."""
    res_end = calculate_future_value(
        principal=Decimal("0.00"),
        annual_rate=Decimal("0.06"),
        years=1,
        monthly_contribution=Decimal("1000.00"),
        compounding_per_year=12,
        contribution_timing="end",
    )
    res_begin = calculate_future_value(
        principal=Decimal("0.00"),
        annual_rate=Decimal("0.06"),
        years=1,
        monthly_contribution=Decimal("1000.00"),
        compounding_per_year=12,
        contribution_timing="begin",
    )
    # Beginning of month contributions earn interest on the first deposit immediately
    assert res_begin.future_value > res_end.future_value
    # Exact: 1000 * ((1.005^12 - 1)/0.005) * 1.005 = 12335.56 vs 12335.56 / 1.005 = 12274.19
    assert res_end.future_value == Decimal("12335.56")
    assert res_begin.future_value == Decimal("12397.24")


def test_calculate_future_value_zero_rate() -> None:
    """Zero rate identity: FV = Principal + Monthly * Months with 0 growth."""
    res = calculate_future_value(
        principal=Decimal("15000.00"),
        annual_rate=Decimal("0.00"),
        years=3,
        monthly_contribution=Decimal("2500.00"),
        compounding_per_year=12,
    )
    expected_total = Decimal("15000.00") + Decimal("2500.00") * Decimal("36")
    assert res.future_value == expected_total
    assert res.total_contributed == expected_total
    assert res.total_growth == Decimal("0.00")


def test_calculate_doubling_time_golden() -> None:
    """Golden test: 8% annual compounding doubles in 9.0065 years (~108 months)."""
    res = calculate_doubling_time(Decimal("0.08"), compounding_per_year=1, rate_type="assumed")
    assert res.years == Decimal("9.0065")
    assert res.months == 108
    assert res.rule_of_72_approx == Decimal("9.0000")
    assert res.assumptions.rate_type == "assumed"


def test_calculate_doubling_time_monthly_compounding() -> None:
    """Golden test: 6% with monthly compounding doubles faster than annual."""
    res_annual = calculate_doubling_time(Decimal("0.06"), compounding_per_year=1)
    res_monthly = calculate_doubling_time(Decimal("0.06"), compounding_per_year=12)
    assert res_monthly.years < res_annual.years
    assert res_monthly.years == Decimal("11.5813")
    assert res_monthly.months == 139


def test_calculate_monthly_required_saving_zero_rate() -> None:
    """Required saving with 0% rate: exact division."""
    res = calculate_monthly_required_saving(
        target=Decimal("120000.00"),
        current=Decimal("0.00"),
        months=12,
        annual_rate=Decimal("0.00"),
    )
    assert res.required_monthly_saving == Decimal("10000.00")
    assert res.shortfall == Decimal("120000.00")
    assert res.total_contributed == Decimal("120000.00")
    assert res.projected_growth == Decimal("0.00")


def test_calculate_monthly_required_saving_with_return() -> None:
    """Required saving with positive rate requires smaller monthly deposits."""
    res_zero = calculate_monthly_required_saving(
        target=Decimal("100000.00"),
        current=Decimal("20000.00"),
        months=24,
        annual_rate=Decimal("0.00"),
    )
    res_growth = calculate_monthly_required_saving(
        target=Decimal("100000.00"),
        current=Decimal("20000.00"),
        months=24,
        annual_rate=Decimal("0.06"),
    )
    assert res_growth.required_monthly_saving < res_zero.required_monthly_saving
    assert res_growth.required_monthly_saving == Decimal("3045.65")
    assert res_growth.projected_growth > Decimal("0.00")


def test_calculate_monthly_required_saving_already_achieved() -> None:
    """If current >= target, required saving is zero."""
    res = calculate_monthly_required_saving(
        target=Decimal("50000.00"),
        current=Decimal("60000.00"),
        months=12,
        annual_rate=Decimal("0.08"),
    )
    assert res.required_monthly_saving == Decimal("0.00")
    assert res.shortfall == Decimal("0.00")


def test_calculate_goal_progress_statuses() -> None:
    """Goal progress status transitions: completed, on_track, at_risk, behind."""
    today = date(2026, 1, 1)

    # 1. Completed
    res_comp = calculate_goal_progress(
        target=Decimal("50000.00"),
        current=Decimal("50000.00"),
        target_date=date(2026, 6, 1),
        today=today,
    )
    assert res_comp.feasibility_status == "completed"
    assert res_comp.is_on_track is True
    assert res_comp.progress_pct == Decimal("100.00")

    # 2. On track (needs 2000/mo, user saves 2500/mo)
    res_ontrack = calculate_goal_progress(
        target=Decimal("50000.00"),
        current=Decimal("30000.00"),
        target_date=date(2026, 11, 1),  # 10 months -> 2000/mo needed
        today=today,
        avg_monthly_saving=Decimal("2500.00"),
    )
    assert res_ontrack.feasibility_status == "on_track"
    assert res_ontrack.is_on_track is True

    # 3. Behind (user saves only 500/mo when 2000/mo is needed)
    res_behind = calculate_goal_progress(
        target=Decimal("50000.00"),
        current=Decimal("30000.00"),
        target_date=date(2026, 11, 1),
        today=today,
        avg_monthly_saving=Decimal("500.00"),
    )
    assert res_behind.feasibility_status == "behind"
    assert res_behind.is_on_track is False


def test_calculate_savings_rate_contract() -> None:
    """Savings rate follows Phase 2 data contract (null for non-positive income)."""
    assert calculate_savings_rate(Decimal("50000.00"), Decimal("12500.00")) == Decimal("25.00")
    assert calculate_savings_rate(Decimal("0.00"), Decimal("500.00")) is None
    assert calculate_savings_rate(Decimal("-1000.00"), Decimal("500.00")) is None


def test_calculate_expense_ratio_contract() -> None:
    """Expense ratio follows data contract (null for non-positive income)."""
    assert calculate_expense_ratio(Decimal("40000.00"), Decimal("30000.00")) == Decimal("75.00")
    assert calculate_expense_ratio(Decimal("0.00"), Decimal("20000.00")) is None


def test_calculate_emergency_fund_tiers() -> None:
    """Emergency reserve coverage tiers: critical, vulnerable, adequate, optimal."""
    essentials = Decimal("20000.00")

    # Critical (< 1 mo)
    res_crit = calculate_emergency_fund(essentials, Decimal("10000.00"))
    assert res_crit.status == "critical"
    assert res_crit.months_covered == Decimal("0.50")

    # Vulnerable (1 to < 3 mo)
    res_vuln = calculate_emergency_fund(essentials, Decimal("40000.00"))
    assert res_vuln.status == "vulnerable"
    assert res_vuln.months_covered == Decimal("2.00")

    # Adequate (3 to < 6 mo)
    res_adeq = calculate_emergency_fund(essentials, Decimal("80000.00"))
    assert res_adeq.status == "adequate"
    assert res_adeq.months_covered == Decimal("4.00")

    # Optimal (>= 6 mo)
    res_opt = calculate_emergency_fund(essentials, Decimal("120000.00"))
    assert res_opt.status == "optimal"
    assert res_opt.months_covered == Decimal("6.00")
    assert res_opt.shortfall == Decimal("0.00")


def test_calculate_affordability_verdicts() -> None:
    """Affordability evaluations across liquid buffers and savings horizon."""
    bal = Decimal("50000.00")
    commitments = Decimal("20000.00")
    goals = Decimal("10000.00")
    surplus = Decimal("5000.00")
    # Available liquidity = 50000 - 30000 = 20000

    # 1. Affordable from cash
    res1 = calculate_affordability(bal, commitments, surplus, Decimal("15000.00"), goals)
    assert res1.is_affordable is True
    assert res1.verdict == "affordable_from_cash"
    assert res1.remaining_buffer == Decimal("5000.00")

    # 2. Affordable with monthly budget (deficit 10,000, surplus 5,000 -> 2 months)
    res2 = calculate_affordability(bal, commitments, surplus, Decimal("30000.00"), goals)
    assert res2.is_affordable is True
    assert res2.verdict == "affordable_with_monthly_budget"
    assert res2.months_to_save_if_deferred == 2

    # 3. Unaffordable cash deficit (deficit 35,000 -> 7 months)
    res3 = calculate_affordability(bal, commitments, surplus, Decimal("55000.00"), goals)
    assert res3.is_affordable is False
    assert res3.verdict == "unaffordable_cash_deficit"
    assert res3.months_to_save_if_deferred == 7

    # 4. Unaffordable zero surplus
    res4 = calculate_affordability(bal, commitments, Decimal("0.00"), Decimal("25000.00"), goals)
    assert res4.is_affordable is False
    assert res4.verdict == "unaffordable_cash_deficit"


def test_run_scenario_simulation() -> None:
    """Scenario comparative simulation projects baseline vs adjustment."""
    base = ScenarioInput(
        initial_balance=Decimal("50000.00"),
        monthly_income=Decimal("60000.00"),
        monthly_expense=Decimal("45000.00"),
        monthly_savings=Decimal("10000.00"),
        annual_return_rate=Decimal("0.05"),
        horizon_years=3,
    )
    overrides = {
        "monthly_savings": Decimal("15000.00"),
        "annual_return_rate": Decimal("0.08"),
    }
    res = run_scenario(base, overrides)
    assert res.simulated_future_value > res.base_future_value
    assert res.net_benefit > Decimal("0.00")
    assert len(res.yearly_comparison) == 3
    assert res.yearly_comparison[0].delta > Decimal("0.00")


# -----------------------------------------------------------------------------
# 3. Edge Cases & Typed Exception Tests
# -----------------------------------------------------------------------------


def test_exceptions_negative_values() -> None:
    """Negative inputs raise NegativeValueError."""
    with pytest.raises(NegativeValueError):
        calculate_future_value(principal=Decimal("-100.00"), annual_rate=Decimal("0.05"), years=1)

    with pytest.raises(NegativeValueError):
        calculate_future_value(
            principal=Decimal("100.00"),
            annual_rate=Decimal("0.05"),
            years=1,
            monthly_contribution=Decimal("-50.00"),
        )

    with pytest.raises(NegativeValueError):
        calculate_monthly_required_saving(
            target=Decimal("-500.00"), current=Decimal("0.00"), months=6
        )

    with pytest.raises(NegativeValueError):
        calculate_savings_rate(income=Decimal("50000.00"), savings=Decimal("-100.00"))


def test_exceptions_zero_or_negative_periods() -> None:
    """Zero or negative periods raise ZeroPeriodError."""
    with pytest.raises(ZeroPeriodError):
        calculate_future_value(principal=Decimal("1000.00"), annual_rate=Decimal("0.05"), years=0)

    with pytest.raises(ZeroPeriodError):
        calculate_monthly_required_saving(
            target=Decimal("1000.00"), current=Decimal("0.00"), months=0
        )

    with pytest.raises(ZeroPeriodError):
        calculate_emergency_fund(
            avg_monthly_essentials=Decimal("1000.00"),
            current_fund=Decimal("500.00"),
            months_target=Decimal("0"),
        )


def test_exceptions_rate_bounds_and_frequencies() -> None:
    """Invalid rates or frequencies raise typed errors."""
    with pytest.raises(InvalidRateError):
        calculate_doubling_time(Decimal("0.00"))

    with pytest.raises(InvalidRateError):
        calculate_doubling_time(Decimal("-0.05"))

    with pytest.raises(InvalidRateError):
        calculate_future_value(principal=Decimal("100.00"), annual_rate=Decimal("15.00"), years=1)

    with pytest.raises(InvalidCompoundingFrequencyError):
        calculate_future_value(
            principal=Decimal("100.00"),
            annual_rate=Decimal("0.05"),
            years=1,
            compounding_per_year=7,
        )

    with pytest.raises(InvalidTimingError):
        calculate_future_value(
            principal=Decimal("100.00"),
            annual_rate=Decimal("0.05"),
            years=1,
            contribution_timing="middle",
        )


def test_exceptions_target_date_in_past() -> None:
    """Target date in past with unpaid shortfall raises InvalidTargetDateError."""
    past_date = date.today() - timedelta(days=30)
    with pytest.raises(InvalidTargetDateError):
        calculate_goal_progress(
            target=Decimal("10000.00"), current=Decimal("5000.00"), target_date=past_date
        )


# -----------------------------------------------------------------------------
# 4. Property-Based Tests (Hypothesis)
# -----------------------------------------------------------------------------


@given(
    principal=st.decimals(min_value=Decimal("100"), max_value=Decimal("1000000"), places=2),
    rate_1=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("0.10"), places=4),
    rate_2=st.decimals(min_value=Decimal("0.11"), max_value=Decimal("0.25"), places=4),
    years=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=30)
def test_property_monotonicity_in_rate(
    principal: Decimal,
    rate_1: Decimal,
    rate_2: Decimal,
    years: int,
) -> None:
    """Property: Increasing the annual rate strictly increases or preserves future value."""
    fv1 = calculate_future_value(principal, rate_1, years).future_value
    fv2 = calculate_future_value(principal, rate_2, years).future_value
    assert fv1 <= fv2


@given(
    principal=st.decimals(min_value=Decimal("100"), max_value=Decimal("500000"), places=2),
    contribution=st.decimals(min_value=Decimal("100"), max_value=Decimal("50000"), places=2),
    rate=st.decimals(min_value=Decimal("0.00"), max_value=Decimal("0.20"), places=4),
    years_1=st.integers(min_value=1, max_value=5),
    years_2=st.integers(min_value=6, max_value=15),
)
@settings(max_examples=30)
def test_property_monotonicity_in_time(
    principal: Decimal,
    contribution: Decimal,
    rate: Decimal,
    years_1: int,
    years_2: int,
) -> None:
    """Property: For r >= 0 and m >= 0, longer horizon strictly increases or preserves future value."""
    fv1 = calculate_future_value(
        principal, rate, years_1, monthly_contribution=contribution
    ).future_value
    fv2 = calculate_future_value(
        principal, rate, years_2, monthly_contribution=contribution
    ).future_value
    assert fv1 <= fv2


@given(
    principal=st.decimals(min_value=Decimal("0"), max_value=Decimal("1000000"), places=2),
    contribution=st.decimals(min_value=Decimal("0"), max_value=Decimal("100000"), places=2),
    rate=st.decimals(min_value=Decimal("0.00"), max_value=Decimal("0.30"), places=4),
    years=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=30)
def test_property_future_value_lower_bound(
    principal: Decimal,
    contribution: Decimal,
    rate: Decimal,
    years: int,
) -> None:
    """Property: For all r >= 0, Future Value >= Total Contributed."""
    res = calculate_future_value(principal, rate, years, monthly_contribution=contribution)
    assert res.future_value >= res.total_contributed
    assert res.total_growth >= Decimal("0.00")


@given(
    rate=st.decimals(min_value=Decimal("0.02"), max_value=Decimal("0.30"), places=4),
    freq=st.sampled_from([1, 2, 4, 12]),
)
@settings(max_examples=30)
def test_property_doubling_time_identity(rate: Decimal, freq: int) -> None:
    """Property: Doubling time calculation t satisfies (1 + r/n)^(n*t) ~ 2."""
    res = calculate_doubling_time(rate, compounding_per_year=freq)
    p = Decimal("10000.00")
    fv_res = calculate_future_value(
        principal=p,
        annual_rate=rate,
        years=res.years,
        compounding_per_year=freq,
    )
    # The balance at doubling time should be approximately 2 * P (within 2% tolerance due to discrete rounding)
    ratio = fv_res.future_value / p
    assert Decimal("1.95") <= ratio <= Decimal("2.05")


@given(
    income=st.decimals(min_value=Decimal("1000"), max_value=Decimal("500000"), places=2),
    savings=st.decimals(min_value=Decimal("0"), max_value=Decimal("1000"), places=2),
    factor=st.integers(min_value=2, max_value=10),
)
@settings(max_examples=30)
def test_property_scale_invariance_savings_rate(
    income: Decimal,
    savings: Decimal,
    factor: int,
) -> None:
    """Property: Savings rate is invariant to scalar multiplication of income and savings."""
    sr1 = calculate_savings_rate(income, savings)
    sr2 = calculate_savings_rate(income * Decimal(factor), savings * Decimal(factor))
    assert sr1 == sr2


# -----------------------------------------------------------------------------
# 5. Additional Edge Cases & Granular Coverage
# -----------------------------------------------------------------------------


def test_rounding_utilities() -> None:
    """Test explicit rounding helpers."""
    assert round_currency(Decimal("100.456")) == Decimal("100.46")
    assert round_currency(Decimal("100.454")) == Decimal("100.45")
    assert round_rate(Decimal("0.084567")) == Decimal("0.0846")
    assert round_ratio(Decimal("0.12345678")) == Decimal("0.123457")


def test_exception_string_formatting() -> None:
    """Test exception string representations."""
    err_param = FinancialEngineError("Value invalid", "annual_rate")
    assert str(err_param) == "[annual_rate] Value invalid"
    err_no_param = FinancialEngineError("General engine failure")
    assert str(err_no_param) == "General engine failure"


def test_nan_and_infinite_validation() -> None:
    """NaN and Infinite values raise typed errors."""
    with pytest.raises(InvalidRateError):
        calculate_future_value(principal=Decimal("NaN"), annual_rate=Decimal("0.05"), years=1)

    with pytest.raises(InvalidRateError):
        calculate_future_value(
            principal=Decimal("1000.00"), annual_rate=Decimal("Infinity"), years=1
        )

    with pytest.raises(InvalidRateError):
        calculate_savings_rate(Decimal("NaN"), Decimal("100.00"))

    with pytest.raises(InvalidRateError):
        calculate_expense_ratio(Decimal("Infinity"), Decimal("100.00"))

    with pytest.raises(InvalidRateError):
        calculate_affordability(
            balance=Decimal("1000.00"),
            upcoming_commitments=Decimal("100.00"),
            avg_monthly_surplus=Decimal("NaN"),
            amount=Decimal("500.00"),
        )

    with pytest.raises(NegativeValueError):
        calculate_affordability(
            balance=Decimal("1000.00"),
            upcoming_commitments=Decimal("100.00"),
            avg_monthly_surplus=Decimal("100.00"),
            amount=Decimal("0.00"),
        )


def test_calculate_future_value_compounding_frequencies() -> None:
    """Test daily compounding (365) and annual compounding (1) with contributions."""
    res_daily = calculate_future_value(
        principal=Decimal("10000.00"),
        annual_rate=Decimal("0.08"),
        years=1,
        compounding_per_year=365,
    )
    # Daily compounding yields slightly more than monthly (10830.00)
    assert res_daily.future_value >= Decimal("10830.00")

    res_annual_contrib = calculate_future_value(
        principal=Decimal("1000.00"),
        annual_rate=Decimal("0.06"),
        years=1,
        monthly_contribution=Decimal("500.00"),
        compounding_per_year=1,
    )
    assert res_annual_contrib.future_value > Decimal("7000.00")


def test_calculate_future_value_sub_year_clamp() -> None:
    """Sub-year period with very small horizon clamps total_months to minimum 1."""
    res = calculate_future_value(
        principal=Decimal("1000.00"),
        annual_rate=Decimal("0.05"),
        years=Decimal("0.05"),
    )
    assert res.assumptions.metadata["total_months"] == 1


def test_calculate_doubling_time_bounds() -> None:
    """Doubling time bounds checking."""
    with pytest.raises(InvalidRateError):
        calculate_doubling_time(Decimal("15.00"))

    with pytest.raises(InvalidCompoundingFrequencyError):
        calculate_doubling_time(Decimal("0.08"), compounding_per_year=5)


def test_calculate_monthly_required_saving_existing_funds_sufficient() -> None:
    """When existing balance grows to exceed target, required contribution is 0."""
    res = calculate_monthly_required_saving(
        target=Decimal("10000.00"),
        current=Decimal("9500.00"),
        months=24,
        annual_rate=Decimal("0.10"),
    )
    assert res.required_monthly_saving == Decimal("0.00")
    assert res.total_contributed == Decimal("0.00")
    assert res.projected_growth > Decimal("0.00")


def test_calculate_monthly_required_saving_timing_begin() -> None:
    """Annuity due ('begin') requires slightly lower monthly contributions than 'end'."""
    res_end = calculate_monthly_required_saving(
        target=Decimal("100000.00"),
        current=Decimal("10000.00"),
        months=24,
        annual_rate=Decimal("0.06"),
        contribution_timing="end",
    )
    res_begin = calculate_monthly_required_saving(
        target=Decimal("100000.00"),
        current=Decimal("10000.00"),
        months=24,
        annual_rate=Decimal("0.06"),
        contribution_timing="begin",
    )
    assert res_begin.required_monthly_saving < res_end.required_monthly_saving

    with pytest.raises(InvalidTimingError):
        calculate_monthly_required_saving(
            target=Decimal("100000.00"),
            current=Decimal("10000.00"),
            months=24,
            contribution_timing="start",
        )

    with pytest.raises(InvalidRateError):
        calculate_monthly_required_saving(
            target=Decimal("100000.00"),
            current=Decimal("10000.00"),
            months=24,
            annual_rate=Decimal("15.00"),
        )


def test_calculate_goal_progress_edge_cases() -> None:
    """Goal progress validations, at_risk status, and no observed saving."""
    today = date(2026, 1, 1)

    with pytest.raises(NegativeValueError):
        calculate_goal_progress(
            target=Decimal("0.00"), current=Decimal("0.00"), target_date=date(2026, 12, 1)
        )

    with pytest.raises(NegativeValueError):
        calculate_goal_progress(
            target=Decimal("50000.00"),
            current=Decimal("10000.00"),
            target_date=date(2026, 12, 1),
            avg_monthly_saving=Decimal("-100.00"),
        )

    # Goal with no saving velocity -> at_risk if months remaining
    res_nosave = calculate_goal_progress(
        target=Decimal("50000.00"),
        current=Decimal("10000.00"),
        target_date=date(2026, 12, 1),
        today=today,
        avg_monthly_saving=None,
    )
    assert res_nosave.feasibility_status == "at_risk"
    assert res_nosave.projected_completion_date is None

    # Goal slightly delayed (needs 12 months, target is 11 months -> at_risk)
    res_at_risk = calculate_goal_progress(
        target=Decimal("60000.00"),
        current=Decimal("0.00"),
        target_date=date(2026, 11, 1),  # 10 months
        today=today,
        avg_monthly_saving=Decimal(
            "5000.00"
        ),  # 60000 / 5000 = 12 months (exceeds 10 by 2 -> at_risk)
    )
    assert res_at_risk.feasibility_status == "at_risk"


def test_calculate_emergency_fund_zero_essentials() -> None:
    """Zero essentials handling: optimal if fund > 0, critical if fund == 0."""
    res_pos = calculate_emergency_fund(Decimal("0.00"), Decimal("5000.00"))
    assert res_pos.months_covered == Decimal("999.00")
    assert res_pos.status == "optimal"

    res_zero = calculate_emergency_fund(Decimal("0.00"), Decimal("0.00"))
    assert res_zero.months_covered == Decimal("0.00")
    assert res_zero.status == "critical"


def test_calculate_affordability_negative_surplus() -> None:
    """Negative surplus causes unaffordable_cash_deficit with no projection."""
    res = calculate_affordability(
        balance=Decimal("20000.00"),
        upcoming_commitments=Decimal("15000.00"),
        avg_monthly_surplus=Decimal("-2500.00"),
        amount=Decimal("10000.00"),
    )
    assert res.is_affordable is False
    assert res.verdict == "unaffordable_cash_deficit"
    assert res.months_to_save_if_deferred is None


def test_run_scenario_validations() -> None:
    """Scenario validations for horizons and overrides."""
    base = ScenarioInput(
        initial_balance=Decimal("10000.00"),
        monthly_income=Decimal("50000.00"),
        monthly_expense=Decimal("40000.00"),
        monthly_savings=Decimal("10000.00"),
        annual_return_rate=Decimal("0.06"),
        horizon_years=5,
    )
    with pytest.raises(ZeroPeriodError):
        run_scenario(
            ScenarioInput(
                initial_balance=Decimal("10000.00"),
                monthly_income=Decimal("50000.00"),
                monthly_expense=Decimal("40000.00"),
                monthly_savings=Decimal("10000.00"),
                horizon_years=0,
            )
        )

    with pytest.raises(ZeroPeriodError):
        run_scenario(base, overrides={"horizon_years": 0})

    with pytest.raises(NegativeValueError):
        run_scenario(base, overrides={"initial_balance": Decimal("-500.00")})


def test_calculator_facade_coverage() -> None:
    """Test backwards-compatible facade functions in calculator.py."""
    from app.financial.calculator import (
        calculate_future_value as facade_fv,
    )
    from app.financial.calculator import (
        calculate_savings_rate as facade_sr,
    )

    assert facade_fv(Decimal("-100.00"), Decimal("0.08"), 12) == Decimal("0.00")
    assert facade_fv(Decimal("5000.00"), Decimal("0.08"), 0) == Decimal("5000.00")
    assert facade_fv(Decimal("10000.00"), Decimal("0.08"), 12) == Decimal("10830.00")
    assert facade_sr(Decimal("50000.00"), Decimal("-100.00")) == Decimal("0.00")
    assert facade_sr(Decimal("0.00"), Decimal("100.00")) == Decimal("0.00")
    assert facade_sr(Decimal("-1000.00"), Decimal("100.00")) == Decimal("0.00")
    assert facade_sr(Decimal("50000.00"), Decimal("10000.00")) == Decimal("20.00")


def test_affordability_fractional_month_clamp() -> None:
    """Affordability clamp months_to_save to minimum 1 when deficit < surplus."""
    res = calculate_affordability(
        balance=Decimal("10000.00"),
        upcoming_commitments=Decimal("9500.00"),
        avg_monthly_surplus=Decimal("1000.00"),
        amount=Decimal("600.00"),
    )
    # Available = 500, Amount = 600 -> Deficit = 100, Surplus = 1000 -> 1 month
    assert res.is_affordable is True
    assert res.verdict == "affordable_with_monthly_budget"
    assert res.months_to_save_if_deferred == 1
