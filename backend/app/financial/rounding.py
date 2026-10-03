"""Explicit rounding policy for deterministic financial calculations.

Policy:
- Currency amounts (BDT) are quantized to 2 decimal places using ROUND_HALF_UP.
- Rates, ratios, and percentages are quantized to 4 or 6 decimal places using ROUND_HALF_UP.
- Decimal arithmetic uses high precision (minimum 28 significant digits).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

# Precision targets
CURRENCY_PRECISION = Decimal("0.01")
RATE_PRECISION = Decimal("0.0001")
RATIO_HIGH_PRECISION = Decimal("0.000001")


def round_currency(value: Decimal) -> Decimal:
    """Round monetary value in BDT to 2 decimal places using ROUND_HALF_UP."""
    return value.quantize(CURRENCY_PRECISION, rounding=ROUND_HALF_UP)


def round_rate(value: Decimal) -> Decimal:
    """Round interest rate or percentage to 4 decimal places using ROUND_HALF_UP."""
    return value.quantize(RATE_PRECISION, rounding=ROUND_HALF_UP)


def round_ratio(value: Decimal) -> Decimal:
    """Round ratio to 6 decimal places using ROUND_HALF_UP."""
    return value.quantize(RATIO_HIGH_PRECISION, rounding=ROUND_HALF_UP)
