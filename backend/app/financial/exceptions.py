"""Strongly typed exceptions for the deterministic financial engine.

Pure Python, zero external dependencies.
"""

from __future__ import annotations


class FinancialEngineError(Exception):
    """Base exception for all financial engine calculation errors."""

    def __init__(self, message: str, parameter: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.parameter = parameter

    def __str__(self) -> str:
        if self.parameter:
            return f"[{self.parameter}] {self.message}"
        return self.message


class NegativeValueError(FinancialEngineError):
    """Raised when a monetary or financial parameter is strictly negative where forbidden."""

    def __init__(self, parameter: str, value: object) -> None:
        super().__init__(
            f"Value for parameter '{parameter}' cannot be negative (received {value}).",
            parameter=parameter,
        )
        self.value = value


class ZeroPeriodError(FinancialEngineError):
    """Raised when a time period (months, years) is zero or negative."""

    def __init__(self, parameter: str, value: object) -> None:
        super().__init__(
            f"Time horizon for '{parameter}' must be strictly positive (received {value}).",
            parameter=parameter,
        )
        self.value = value


class InvalidRateError(FinancialEngineError):
    """Raised when an interest or growth rate is invalid (e.g., negative, NaN, infinite, or exceeding bounds)."""

    def __init__(self, message: str, parameter: str = "annual_rate") -> None:
        super().__init__(message, parameter=parameter)


class InvalidCompoundingFrequencyError(FinancialEngineError):
    """Raised when compounding frequency per year is not an approved discrete frequency."""

    def __init__(self, frequency: int, allowed: list[int] | tuple[int, ...]) -> None:
        super().__init__(
            f"Invalid compounding frequency {frequency}. Allowed frequencies: {list(allowed)}",
            parameter="compounding_per_year",
        )
        self.frequency = frequency
        self.allowed = allowed


class InvalidTimingError(FinancialEngineError):
    """Raised when contribution timing is not 'end' or 'begin'."""

    def __init__(self, timing: str) -> None:
        super().__init__(
            f"Invalid contribution timing '{timing}'. Must be 'end' (ordinary annuity) or 'begin' (annuity due).",
            parameter="contribution_timing",
        )
        self.timing = timing


class InvalidTargetDateError(FinancialEngineError):
    """Raised when a financial goal target date is in the past or precedes today."""

    def __init__(self, message: str) -> None:
        super().__init__(message, parameter="target_date")
