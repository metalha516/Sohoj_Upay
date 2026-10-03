"""Unit tests for the pure financial engine."""

from decimal import Decimal

from app.financial.calculator import calculate_future_value, calculate_savings_rate


def test_calculate_savings_rate() -> None:
    """Test savings rate percentage calculation."""
    income = Decimal("50000.00")
    savings = Decimal("10000.00")
    rate = calculate_savings_rate(income, savings)
    assert rate == Decimal("20.00")

    # Zero or negative income edge case
    assert calculate_savings_rate(Decimal("0.00"), Decimal("500.00")) == Decimal("0.00")
    assert calculate_savings_rate(Decimal("-100.00"), Decimal("500.00")) == Decimal("0.00")


def test_calculate_future_value() -> None:
    """Test compound interest calculation with monthly compounding."""
    principal = Decimal("10000.00")
    annual_rate = Decimal("0.08")  # 8% annual
    months = 12

    fv = calculate_future_value(principal, annual_rate, months)
    # Expected FV = 10000 * (1 + 0.08/12)^12 = 10829.995... -> 10830.00
    assert fv == Decimal("10830.00")
