"""Pure deterministic financial calculation engine using Decimal arithmetic.

Adheres strictly to design.md §6:
- Exact Decimal arithmetic with explicit ROUND_HALF_UP rounding policy.
- Zero dependencies on DB, ORM, ML, or AI layers.
- Typed dataclass results containing an assumptions block with mandatory rate_type.
- Zero-rate special cases, end/begin contribution timing, and discrete compounding frequencies.
"""

from __future__ import annotations

import calendar
from datetime import date
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal, localcontext
from typing import Any, cast

from app.financial.exceptions import (
    InvalidCompoundingFrequencyError,
    InvalidRateError,
    InvalidTargetDateError,
    InvalidTimingError,
    NegativeValueError,
    ZeroPeriodError,
)
from app.financial.rounding import round_currency, round_rate
from app.financial.schemas import (
    AffordabilityResult,
    AssumptionsBlock,
    DoublingResult,
    EmergencyFundResult,
    FVResult,
    GoalProgressResult,
    RateType,
    RequiredSavingResult,
    ScenarioInput,
    ScenarioResult,
    ScenarioYearPoint,
    YearlyPoint,
)

# Approved discrete compounding frequencies per year
ALLOWED_COMPOUNDING_FREQUENCIES: tuple[int, ...] = (1, 2, 4, 12, 365)
MAX_PLAUSIBLE_RATE = Decimal("10.00")  # 1000% annual


def _validate_decimal(val: Decimal, param_name: str, allow_negative: bool = False) -> None:
    """Validate that a Decimal is finite, not NaN, and within positivity constraints."""
    if val.is_nan() or val.is_infinite():
        raise InvalidRateError(
            f"Parameter '{param_name}' cannot be NaN or infinite.", parameter=param_name
        )
    if not allow_negative and val < Decimal("0"):
        if "rate" in param_name:
            raise InvalidRateError(
                f"Rate parameter '{param_name}' cannot be negative (received {val}).",
                parameter=param_name,
            )
        raise NegativeValueError(param_name, val)


def calculate_future_value(
    principal: Decimal,
    annual_rate: Decimal,
    years: Decimal | int,
    monthly_contribution: Decimal = Decimal("0.00"),
    compounding_per_year: int = 12,
    contribution_timing: str = "end",
    rate_type: RateType = "assumed",
    inflation_adjusted: bool = False,
) -> FVResult:
    """Calculate compound growth and future value with periodic monthly deposits.

    Formulas:
    - Lump Sum: A = P * (1 + r/n)^(n*t)
    - Monthly Contributions (frequency p = 12):
        Effective monthly rate i_m = (1 + r/n)^(n/12) - 1   (for n=12, i_m = r/12)
        If timing == 'end':   FV_m = m * [((1 + i_m)^M - 1) / i_m]
        If timing == 'begin': FV_m = m * [((1 + i_m)^M - 1) / i_m] * (1 + i_m)
    - Zero-Rate Special Case (r = 0):
        FV = P + m * M
        Growth = 0.00

    Args:
        principal: Starting principal amount (BDT). Must be >= 0.
        annual_rate: Annual nominal interest/growth rate (e.g. Decimal("0.08") for 8%).
        years: Time horizon in years (Decimal or int, > 0).
        monthly_contribution: Recurring deposit at each month end/begin.
        compounding_per_year: Compounding frequency per year (1, 2, 4, 12, 365).
        contribution_timing: 'end' (ordinary annuity) or 'begin' (annuity due).
        rate_type: Mandatory audit classification ("assumed", "historical", "contractual").
        inflation_adjusted: Flag indicating real vs nominal valuation.

    Returns:
        FVResult dataclass with totals, assumptions block, and yearly series.
    """
    _validate_decimal(principal, "principal", allow_negative=False)
    _validate_decimal(annual_rate, "annual_rate", allow_negative=False)
    _validate_decimal(monthly_contribution, "monthly_contribution", allow_negative=False)

    years_dec = Decimal(str(years))
    _validate_decimal(years_dec, "years", allow_negative=False)
    if years_dec <= Decimal("0"):
        raise ZeroPeriodError("years", years)

    if annual_rate > MAX_PLAUSIBLE_RATE:
        raise InvalidRateError(
            f"Annual rate {annual_rate} exceeds plausible maximum of {MAX_PLAUSIBLE_RATE} (1000%).",
            parameter="annual_rate",
        )

    if compounding_per_year not in ALLOWED_COMPOUNDING_FREQUENCIES:
        raise InvalidCompoundingFrequencyError(
            compounding_per_year, ALLOWED_COMPOUNDING_FREQUENCIES
        )

    if contribution_timing not in ("end", "begin"):
        raise InvalidTimingError(contribution_timing)

    with localcontext() as ctx:
        ctx.prec = 35  # High-precision internal workspace

        total_months = int((years_dec * Decimal("12")).to_integral_value(rounding=ROUND_HALF_UP))
        if total_months < 1:
            total_months = 1

        n_dec = Decimal(compounding_per_year)

        # Calculate effective monthly rate i_m
        if annual_rate == Decimal("0"):
            eff_monthly_rate = Decimal("0")
        elif compounding_per_year == 12:
            eff_monthly_rate = annual_rate / Decimal("12")
        else:
            base_factor = Decimal("1") + (annual_rate / n_dec)
            power_exp = n_dec / Decimal("12")
            eff_monthly_rate = (base_factor**power_exp) - Decimal("1")

        def _calc_balance_at_months(m_count: int) -> tuple[Decimal, Decimal]:
            """Compute (balance, total_contributed) at specific month count."""
            m_dec = Decimal(m_count)
            tot_contributed = principal + (monthly_contribution * m_dec)

            if annual_rate == Decimal("0"):
                return tot_contributed, tot_contributed

            # Lump sum growth
            lump_growth = principal * ((Decimal("1") + eff_monthly_rate) ** m_dec)

            # Contribution growth
            if monthly_contribution > Decimal("0"):
                annuity_factor = (
                    ((Decimal("1") + eff_monthly_rate) ** m_dec) - Decimal("1")
                ) / eff_monthly_rate
                if contribution_timing == "begin":
                    annuity_factor = annuity_factor * (Decimal("1") + eff_monthly_rate)
                contrib_growth = monthly_contribution * annuity_factor
            else:
                contrib_growth = Decimal("0")

            total_bal = lump_growth + contrib_growth
            return total_bal, tot_contributed

        # Yearly breakdown series
        series: list[YearlyPoint] = []
        full_years = int(years_dec)
        for y in range(1, full_years + 1):
            y_months = y * 12
            bal, cont = _calc_balance_at_months(y_months)
            grw = max(Decimal("0.00"), bal - cont)
            series.append(
                YearlyPoint(
                    year=y,
                    balance=round_currency(bal),
                    contributions=round_currency(cont),
                    growth=round_currency(grw),
                )
            )

        # Final totals at target horizon
        final_bal, final_cont = _calc_balance_at_months(total_months)
        total_cont_rounded = round_currency(final_cont)
        fv_rounded = round_currency(final_bal)
        growth_rounded = round_currency(max(Decimal("0.00"), fv_rounded - total_cont_rounded))

        assumptions = AssumptionsBlock(
            rate_type=rate_type,
            annual_rate=annual_rate,
            compounding_per_year=compounding_per_year,
            contribution_timing=contribution_timing,
            inflation_adjusted=inflation_adjusted,
            metadata={
                "total_months": total_months,
                "effective_monthly_rate": str(eff_monthly_rate),
            },
        )

        return FVResult(
            future_value=fv_rounded,
            total_contributed=total_cont_rounded,
            total_growth=growth_rounded,
            assumptions=assumptions,
            series=series,
            disclaimer_code="PROJECTION_NOT_GUARANTEED",
        )


def calculate_doubling_time(
    annual_rate: Decimal,
    compounding_per_year: int = 1,
    rate_type: RateType = "assumed",
) -> DoublingResult:
    """Calculate exact time required to double capital at given compound rate.

    Formula:
        t = ln(2) / [n * ln(1 + r/n)]
    Rule of 72 Approximation:
        t_approx = 72 / (r * 100)

    Args:
        annual_rate: Annual nominal rate (> 0).
        compounding_per_year: Compounding frequency (1, 2, 4, 12, 365).
        rate_type: Audit classification ("assumed", "historical", "contractual").

    Returns:
        DoublingResult dataclass with exact years, months, and approximation.
    """
    _validate_decimal(annual_rate, "annual_rate", allow_negative=False)
    if annual_rate <= Decimal("0"):
        raise InvalidRateError(
            "Annual rate must be strictly positive (> 0) to double capital.",
            parameter="annual_rate",
        )
    if annual_rate > MAX_PLAUSIBLE_RATE:
        raise InvalidRateError(
            f"Annual rate {annual_rate} exceeds maximum of {MAX_PLAUSIBLE_RATE}.",
            parameter="annual_rate",
        )

    if compounding_per_year not in ALLOWED_COMPOUNDING_FREQUENCIES:
        raise InvalidCompoundingFrequencyError(
            compounding_per_year, ALLOWED_COMPOUNDING_FREQUENCIES
        )

    with localcontext() as ctx:
        ctx.prec = 35

        n_dec = Decimal(compounding_per_year)
        periodic_rate = annual_rate / n_dec
        ln_2 = Decimal("2").ln()
        ln_factor = (Decimal("1") + periodic_rate).ln()
        t_years = ln_2 / (n_dec * ln_factor)

        # Rule of 72 approximation
        rate_percent = annual_rate * Decimal("100")
        rule_72 = Decimal("72") / rate_percent

        months = int((t_years * Decimal("12")).to_integral_value(rounding=ROUND_HALF_UP))

        assumptions = AssumptionsBlock(
            rate_type=rate_type,
            annual_rate=annual_rate,
            compounding_per_year=compounding_per_year,
            metadata={"rule_of_72": str(round_rate(rule_72))},
        )

        return DoublingResult(
            years=round_rate(t_years),
            months=months,
            annual_rate=annual_rate,
            compounding_per_year=compounding_per_year,
            rule_of_72_approx=round_rate(rule_72),
            assumptions=assumptions,
            disclaimer_code="PROJECTION_NOT_GUARANTEED",
        )


def calculate_monthly_required_saving(
    target: Decimal,
    current: Decimal,
    months: int,
    annual_rate: Decimal = Decimal("0.00"),
    rate_type: RateType = "assumed",
    contribution_timing: str = "end",
) -> RequiredSavingResult:
    """Calculate the fixed monthly deposit needed to reach a target sum.

    Formulas:
    - Zero Rate (r = 0):
        required = (target - current) / months
    - Positive Rate (r > 0, compounding monthly):
        i = r / 12
        FV_current = current * (1 + i)^n
        Remaining needed Rem = target - FV_current
        If timing == 'end':   required = Rem * i / ((1 + i)^n - 1)
        If timing == 'begin': required = Rem * i / [((1 + i)^n - 1) * (1 + i)]

    Args:
        target: Target amount (BDT, >= 0).
        current: Starting amount already accumulated (BDT, >= 0).
        months: Number of months remaining (int, > 0).
        annual_rate: Expected annual growth rate (Decimal, >= 0).
        rate_type: Audit classification ("assumed", "historical", "contractual").
        contribution_timing: 'end' or 'begin'.

    Returns:
        RequiredSavingResult dataclass.
    """
    _validate_decimal(target, "target", allow_negative=False)
    _validate_decimal(current, "current", allow_negative=False)
    _validate_decimal(annual_rate, "annual_rate", allow_negative=False)

    if months <= 0:
        raise ZeroPeriodError("months", months)

    if annual_rate > MAX_PLAUSIBLE_RATE:
        raise InvalidRateError(
            f"Annual rate {annual_rate} exceeds maximum of {MAX_PLAUSIBLE_RATE}.",
            parameter="annual_rate",
        )

    if contribution_timing not in ("end", "begin"):
        raise InvalidTimingError(contribution_timing)

    shortfall = max(Decimal("0.00"), target - current)

    # If target already attained
    if target <= current:
        assumptions = AssumptionsBlock(
            rate_type=rate_type,
            annual_rate=annual_rate,
            compounding_per_year=12,
            contribution_timing=contribution_timing,
        )
        return RequiredSavingResult(
            required_monthly_saving=Decimal("0.00"),
            target_amount=round_currency(target),
            current_amount=round_currency(current),
            shortfall=Decimal("0.00"),
            months=months,
            total_contributed=Decimal("0.00"),
            projected_growth=Decimal("0.00"),
            assumptions=assumptions,
            disclaimer_code="PROJECTION_NOT_GUARANTEED",
        )

    with localcontext() as ctx:
        ctx.prec = 35
        m_dec = Decimal(months)

        if annual_rate == Decimal("0"):
            required_m = round_currency(shortfall / m_dec)
            tot_contrib = round_currency(required_m * m_dec)
            proj_growth = Decimal("0.00")
        else:
            i = annual_rate / Decimal("12")
            growth_factor = (Decimal("1") + i) ** m_dec
            fv_current = current * growth_factor

            if fv_current >= target:
                # Existing funds will compound to hit the target on their own
                required_m = Decimal("0.00")
                tot_contrib = Decimal("0.00")
                proj_growth = round_currency(fv_current - current)
            else:
                rem_needed = target - fv_current
                annuity_denom = growth_factor - Decimal("1")
                if contribution_timing == "begin":
                    annuity_denom = annuity_denom * (Decimal("1") + i)

                raw_required = (rem_needed * i) / annuity_denom
                required_m = round_currency(raw_required)
                tot_contrib = round_currency(required_m * m_dec)
                proj_growth = round_currency(max(Decimal("0.00"), target - current - tot_contrib))

        assumptions = AssumptionsBlock(
            rate_type=rate_type,
            annual_rate=annual_rate,
            compounding_per_year=12,
            contribution_timing=contribution_timing,
        )

        return RequiredSavingResult(
            required_monthly_saving=required_m,
            target_amount=round_currency(target),
            current_amount=round_currency(current),
            shortfall=round_currency(shortfall),
            months=months,
            total_contributed=tot_contrib,
            projected_growth=proj_growth,
            assumptions=assumptions,
            disclaimer_code="PROJECTION_NOT_GUARANTEED",
        )


def calculate_goal_progress(
    target: Decimal,
    current: Decimal,
    target_date: date,
    today: date | None = None,
    avg_monthly_saving: Decimal | None = None,
) -> GoalProgressResult:
    """Assess progress and trajectory toward a scheduled financial goal.

    Args:
        target: Target amount (BDT, > 0).
        current: Amount accumulated to date (BDT, >= 0).
        target_date: Planned completion date.
        today: Reference date (defaults to date.today()).
        avg_monthly_saving: Observed average monthly contribution rate.

    Returns:
        GoalProgressResult dataclass.
    """
    _validate_decimal(target, "target", allow_negative=False)
    _validate_decimal(current, "current", allow_negative=False)
    if target <= Decimal("0"):
        raise NegativeValueError("target", target)

    if today is None:
        today = date.today()

    if avg_monthly_saving is not None:
        _validate_decimal(avg_monthly_saving, "avg_monthly_saving", allow_negative=False)

    shortfall = max(Decimal("0.00"), target - current)
    progress_pct = round_rate(min(Decimal("100.00"), (current / target) * Decimal("100")))

    # Calendar months remaining
    month_delta = (target_date.year - today.year) * 12 + (target_date.month - today.month)
    months_remaining = 1 if target_date > today and month_delta == 0 else max(0, month_delta)

    if target_date <= today and shortfall > Decimal("0.00"):
        raise InvalidTargetDateError(
            f"Target date {target_date.isoformat()} has passed while shortfall of ৳{shortfall:,.2f} remains."
        )

    # Goal already fulfilled
    if shortfall == Decimal("0.00"):
        return GoalProgressResult(
            target_amount=round_currency(target),
            current_amount=round_currency(current),
            shortfall=Decimal("0.00"),
            progress_pct=Decimal("100.00"),
            months_remaining=months_remaining,
            is_on_track=True,
            projected_completion_date=today,
            required_monthly_saving=Decimal("0.00"),
            current_monthly_saving=avg_monthly_saving,
            feasibility_status="completed",
        )

    # Required monthly saving to meet target by target_date
    if months_remaining > 0:
        required_m = round_currency(shortfall / Decimal(months_remaining))
    else:
        required_m = round_currency(shortfall)

    # Projection based on observed saving velocity
    projected_date: date | None = None
    is_on_track = False
    feasibility: str

    if avg_monthly_saving is None or avg_monthly_saving <= Decimal("0.00"):
        is_on_track = False
        feasibility = "at_risk" if months_remaining > 0 else "behind"
        projected_date = None
    else:
        months_needed = int(
            (shortfall / avg_monthly_saving).to_integral_value(rounding=ROUND_CEILING)
        )
        if months_needed < 1:
            months_needed = 1

        new_month = today.month + months_needed
        new_year = today.year + (new_month - 1) // 12
        new_month = ((new_month - 1) % 12) + 1
        max_day = calendar.monthrange(new_year, new_month)[1]
        new_day = min(today.day, max_day)
        projected_date = date(new_year, new_month, new_day)

        if projected_date <= target_date:
            is_on_track = True
            feasibility = "on_track"
        elif months_needed <= months_remaining + 2:
            is_on_track = False
            feasibility = "at_risk"
        else:
            is_on_track = False
            feasibility = "behind"

    return GoalProgressResult(
        target_amount=round_currency(target),
        current_amount=round_currency(current),
        shortfall=round_currency(shortfall),
        progress_pct=progress_pct,
        months_remaining=months_remaining,
        is_on_track=is_on_track,
        projected_completion_date=projected_date,
        required_monthly_saving=required_m,
        current_monthly_saving=avg_monthly_saving,
        feasibility_status=cast(Any, feasibility),
    )


def calculate_savings_rate(income: Decimal, savings: Decimal) -> Decimal | None:
    """Calculate the savings rate percentage per data-contract.md §1.2.

    Formula:
        SR = (Savings / Income) * 100 if Income > 0 else None
    """
    _validate_decimal(savings, "savings", allow_negative=False)
    if income.is_nan() or income.is_infinite():
        raise InvalidRateError("Income cannot be NaN or infinite", parameter="income")

    if income <= Decimal("0"):
        return None

    rate = (savings / income) * Decimal("100")
    return round_currency(rate)


def calculate_expense_ratio(income: Decimal, expense: Decimal) -> Decimal | None:
    """Calculate the expense-to-income percentage.

    Formula:
        ExpenseRatio = (Expense / Income) * 100 if Income > 0 else None
    """
    _validate_decimal(expense, "expense", allow_negative=False)
    if income.is_nan() or income.is_infinite():
        raise InvalidRateError("Income cannot be NaN or infinite", parameter="income")

    if income <= Decimal("0"):
        return None

    ratio = (expense / income) * Decimal("100")
    return round_currency(ratio)


def calculate_emergency_fund(
    avg_monthly_essentials: Decimal,
    current_fund: Decimal,
    months_target: Decimal = Decimal("6.0"),
) -> EmergencyFundResult:
    """Evaluate liquid emergency buffer sufficiency against essential expenditures.

    Threshold tiers:
    - critical: < 1 month coverage
    - vulnerable: 1 to < 3 months coverage
    - adequate: 3 to < months_target coverage
    - optimal: >= months_target coverage
    """
    _validate_decimal(avg_monthly_essentials, "avg_monthly_essentials", allow_negative=False)
    _validate_decimal(current_fund, "current_fund", allow_negative=False)
    _validate_decimal(months_target, "months_target", allow_negative=False)

    if months_target <= Decimal("0"):
        raise ZeroPeriodError("months_target", months_target)

    target_fund = round_currency(avg_monthly_essentials * months_target)
    shortfall = round_currency(max(Decimal("0.00"), target_fund - current_fund))

    if avg_monthly_essentials == Decimal("0"):
        months_covered = Decimal("999.00") if current_fund > Decimal("0") else Decimal("0.00")
    else:
        months_covered = round_currency(current_fund / avg_monthly_essentials)

    if months_covered < Decimal("1.00"):
        status = "critical"
        rec = (
            f"High vulnerability: Your reserve covers only {months_covered} months of essentials. "
            f"Prioritize building ৳{shortfall:,.2f} before extra discretionary spending."
        )
    elif months_covered < Decimal("3.00"):
        status = "vulnerable"
        rec = (
            f"Developing reserve: You have {months_covered} months covered. "
            f"Aim to bridge the remaining ৳{shortfall:,.2f} toward the 3-6 month safety threshold."
        )
    elif months_covered < months_target:
        status = "adequate"
        rec = (
            f"Good baseline: You have {months_covered} months of essential runway. "
            f"An additional ৳{shortfall:,.2f} achieves your full {months_target}-month target."
        )
    else:
        status = "optimal"
        rec = (
            f"Fully protected: Your emergency reserve is fully funded ({months_covered} months). "
            f"Surplus cash can now be channeled toward long-term goals or DPS investments."
        )

    return EmergencyFundResult(
        current_fund=round_currency(current_fund),
        target_fund=target_fund,
        avg_monthly_essentials=round_currency(avg_monthly_essentials),
        months_target=round_rate(months_target),
        months_covered=months_covered,
        shortfall=shortfall,
        status=cast(Any, status),
        recommendation=rec,
    )


def calculate_affordability(
    balance: Decimal,
    upcoming_commitments: Decimal,
    avg_monthly_surplus: Decimal,
    amount: Decimal,
    goals_impact: Decimal = Decimal("0.00"),
) -> AffordabilityResult:
    """Assess whether a discretionary purchase is safe without jeopardizing commitments or goals.

    Verdicts:
    - affordable_from_cash: Can be paid outright from liquid buffer today.
    - affordable_with_monthly_budget: Depletes immediate buffer, but surplus can absorb within <= 3 months.
    - unaffordable_cash_deficit: Severe deficit or negative surplus; risky without debt.
    """
    _validate_decimal(balance, "balance", allow_negative=False)
    _validate_decimal(upcoming_commitments, "upcoming_commitments", allow_negative=False)
    _validate_decimal(goals_impact, "goals_impact", allow_negative=False)
    _validate_decimal(amount, "amount", allow_negative=False)

    if amount <= Decimal("0"):
        raise NegativeValueError("amount", amount)

    if avg_monthly_surplus.is_nan() or avg_monthly_surplus.is_infinite():
        raise InvalidRateError("Surplus cannot be NaN or infinite", parameter="avg_monthly_surplus")

    obligations = upcoming_commitments + goals_impact
    available_liquidity = round_currency(balance - obligations)
    remaining_buffer = round_currency(available_liquidity - amount)

    if remaining_buffer >= Decimal("0.00"):
        return AffordabilityResult(
            is_affordable=True,
            verdict="affordable_from_cash",
            purchase_amount=round_currency(amount),
            current_balance=round_currency(balance),
            upcoming_commitments=round_currency(upcoming_commitments),
            goals_allocation=round_currency(goals_impact),
            available_liquidity=available_liquidity,
            remaining_buffer=remaining_buffer,
            months_to_save_if_deferred=0,
            explanation=(
                f"You can comfortably afford ৳{amount:,.2f} from existing liquidity while preserving all "
                f"commitments (৳{upcoming_commitments:,.2f}) and goal allocations (৳{goals_impact:,.2f}). "
                f"A buffer of ৳{remaining_buffer:,.2f} will remain."
            ),
        )

    # Immediate purchase creates a deficit
    cash_deficit = abs(remaining_buffer)

    if avg_monthly_surplus > Decimal("0.00"):
        months_to_save = int(
            (cash_deficit / avg_monthly_surplus).to_integral_value(rounding=ROUND_CEILING)
        )
        if months_to_save < 1:
            months_to_save = 1

        if months_to_save <= 3:
            return AffordabilityResult(
                is_affordable=True,
                verdict="affordable_with_monthly_budget",
                purchase_amount=round_currency(amount),
                current_balance=round_currency(balance),
                upcoming_commitments=round_currency(upcoming_commitments),
                goals_allocation=round_currency(goals_impact),
                available_liquidity=available_liquidity,
                remaining_buffer=remaining_buffer,
                months_to_save_if_deferred=months_to_save,
                explanation=(
                    f"Immediate purchase would cause an uncommitted deficit of ৳{cash_deficit:,.2f}. "
                    f"However, with your average monthly surplus of ৳{avg_monthly_surplus:,.2f}, you can "
                    f"safely budget for this item by saving over {months_to_save} month(s)."
                ),
            )
        else:
            return AffordabilityResult(
                is_affordable=False,
                verdict="unaffordable_cash_deficit",
                purchase_amount=round_currency(amount),
                current_balance=round_currency(balance),
                upcoming_commitments=round_currency(upcoming_commitments),
                goals_allocation=round_currency(goals_impact),
                available_liquidity=available_liquidity,
                remaining_buffer=remaining_buffer,
                months_to_save_if_deferred=months_to_save,
                explanation=(
                    f"This purchase exceeds your available buffer by ৳{cash_deficit:,.2f}. "
                    f"At your current monthly surplus of ৳{avg_monthly_surplus:,.2f}, it would require "
                    f"{months_to_save} months of saving, which represents significant financial strain."
                ),
            )

    # Negative or zero surplus
    return AffordabilityResult(
        is_affordable=False,
        verdict="unaffordable_cash_deficit",
        purchase_amount=round_currency(amount),
        current_balance=round_currency(balance),
        upcoming_commitments=round_currency(upcoming_commitments),
        goals_allocation=round_currency(goals_impact),
        available_liquidity=available_liquidity,
        remaining_buffer=remaining_buffer,
        months_to_save_if_deferred=None,
        explanation=(
            f"This purchase exceeds your available liquid buffer by ৳{cash_deficit:,.2f}, and you currently "
            f"have no positive monthly surplus (৳{avg_monthly_surplus:,.2f}). Immediate purchase risks debt."
        ),
    )


def run_scenario(
    base: ScenarioInput,
    overrides: dict[str, Any] | None = None,
) -> ScenarioResult:
    """Project and compare multi-year wealth accumulation trajectories under hypothetical adjustments.

    Args:
        base: Starting baseline parameters (initial balance, monthly cash flows, return rate).
        overrides: Dictionary of adjustments to simulate (e.g. increase savings, change return rate).

    Returns:
        ScenarioResult dataclass with yearly comparative points and summary delta.
    """
    _validate_decimal(base.initial_balance, "initial_balance", allow_negative=False)
    _validate_decimal(base.monthly_savings, "monthly_savings", allow_negative=False)
    _validate_decimal(base.annual_return_rate, "annual_return_rate", allow_negative=False)

    if base.horizon_years <= 0:
        raise ZeroPeriodError("horizon_years", base.horizon_years)

    ov = overrides or {}

    # Extract adjusted parameters
    sim_initial = Decimal(str(ov.get("initial_balance", base.initial_balance)))
    sim_savings = Decimal(str(ov.get("monthly_savings", base.monthly_savings)))
    sim_rate = Decimal(str(ov.get("annual_return_rate", base.annual_return_rate)))
    sim_horizon = int(ov.get("horizon_years", base.horizon_years))

    _validate_decimal(sim_initial, "simulated_initial_balance", allow_negative=False)
    _validate_decimal(sim_savings, "simulated_monthly_savings", allow_negative=False)
    _validate_decimal(sim_rate, "simulated_annual_return_rate", allow_negative=False)

    if sim_horizon <= 0:
        raise ZeroPeriodError("horizon_years", sim_horizon)

    horizon = min(base.horizon_years, sim_horizon)

    yearly_comparison: list[ScenarioYearPoint] = []
    for y in range(1, horizon + 1):
        base_fv = calculate_future_value(
            principal=base.initial_balance,
            annual_rate=base.annual_return_rate,
            years=y,
            monthly_contribution=base.monthly_savings,
            compounding_per_year=12,
            rate_type=base.rate_type,
        )
        sim_fv = calculate_future_value(
            principal=sim_initial,
            annual_rate=sim_rate,
            years=y,
            monthly_contribution=sim_savings,
            compounding_per_year=12,
            rate_type=base.rate_type,
        )

        delta = round_currency(sim_fv.future_value - base_fv.future_value)
        yearly_comparison.append(
            ScenarioYearPoint(
                year=y,
                baseline_balance=base_fv.future_value,
                simulated_balance=sim_fv.future_value,
                baseline_growth=base_fv.total_growth,
                simulated_growth=sim_fv.total_growth,
                delta=delta,
            )
        )

    final_base_fv = yearly_comparison[-1].baseline_balance
    final_sim_fv = yearly_comparison[-1].simulated_balance
    net_benefit = round_currency(final_sim_fv - final_base_fv)

    summary = (
        f"Over {horizon} years, the simulated plan accumulates ৳{final_sim_fv:,.2f} compared to "
        f"baseline ৳{final_base_fv:,.2f}, delivering a net advantage of ৳{net_benefit:+,.2f}."
    )

    assumptions = AssumptionsBlock(
        rate_type=base.rate_type,
        annual_rate=sim_rate,
        compounding_per_year=12,
        metadata={
            "baseline_savings": str(base.monthly_savings),
            "simulated_savings": str(sim_savings),
            "baseline_rate": str(base.annual_return_rate),
            "simulated_rate": str(sim_rate),
        },
    )

    return ScenarioResult(
        base_future_value=final_base_fv,
        simulated_future_value=final_sim_fv,
        net_benefit=net_benefit,
        assumptions=assumptions,
        yearly_comparison=yearly_comparison,
        summary=summary,
    )
