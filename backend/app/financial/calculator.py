"""Backwards-compatible convenience helpers for deterministic financial calculations.

Delegates core calculation algorithms to app.financial.engine.
"""

from __future__ import annotations

from decimal import Decimal

from app.financial.engine import (
    calculate_future_value as _engine_fv,
)
from app.financial.engine import (
    calculate_savings_rate as _engine_sr,
)


def calculate_savings_rate(income: Decimal, savings: Decimal) -> Decimal:
    """Calculate savings rate, returning Decimal('0.00') if income is zero or negative."""
    if income <= Decimal("0") or savings < Decimal("0"):
        return Decimal("0.00")
    res = _engine_sr(income, savings)
    if res is None:
        return Decimal("0.00")
    return res


def calculate_future_value(
    principal: Decimal,
    annual_rate: Decimal,
    months: int,
) -> Decimal:
    """Calculate compound future value with monthly compounding over month count."""
    if principal < Decimal("0") or months <= 0:
        return max(principal, Decimal("0.00"))
    years = Decimal(months) / Decimal("12")
    res = _engine_fv(
        principal=principal, annual_rate=annual_rate, years=years, compounding_per_year=12
    )
    return res.future_value
