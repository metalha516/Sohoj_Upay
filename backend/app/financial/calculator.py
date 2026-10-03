"""Pure deterministic financial calculation engine using Decimal arithmetic.

Zero external dependencies (no DB, no ORM, no ML, no LLM).
"""

from decimal import ROUND_HALF_UP, Decimal


def calculate_savings_rate(income: Decimal, savings: Decimal) -> Decimal:
    """Calculate the savings rate as a percentage of total income.

    Formula: (savings / income) * 100
    Returns Decimal rounded to 2 decimal places.
    """
    if income <= Decimal("0"):
        return Decimal("0.00")
    if savings < Decimal("0"):
        return Decimal("0.00")

    rate = (savings / income) * Decimal("100")
    return rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_future_value(
    principal: Decimal,
    annual_rate: Decimal,
    months: int,
) -> Decimal:
    """Calculate compound interest future value with monthly compounding.

    Formula: FV = P * (1 + r/12)^n
    """
    if principal < Decimal("0") or months <= 0:
        return max(principal, Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    monthly_rate = annual_rate / Decimal("12")
    factor = (Decimal("1") + monthly_rate) ** months
    fv = principal * factor
    return fv.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
