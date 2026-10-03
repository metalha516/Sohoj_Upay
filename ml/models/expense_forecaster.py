"""Expense forecasting engine with multi-quantile regression (0.1, 0.5, 0.9),

uncertainty intervals, rolling moving-average fallback, and factor explanations.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from sklearn.ensemble import HistGradientBoostingRegressor


class ForecastOutputContract(BaseModel):
    """Output contract for expense forecasting."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    predicted_expense: float = Field(..., description="Median (p50) point forecast in BDT")
    lower_bound_p10: float = Field(..., description="10th percentile lower bound in BDT")
    upper_bound_p90: float = Field(..., description="90th percentile upper bound in BDT")
    prediction_interval_width: float = Field(
        ..., description="Width of 80% confidence prediction interval"
    )
    fallback_used: bool = Field(
        default=False,
        description="True if moving-average fallback was used due to sparse history",
    )
    model_version: str = Field(default="v1.0.0", description="Model version used for inference")
    target_month: str = Field(..., description="Forecast target horizon month (YYYY-MM)")
    factors: list[dict[str, Any]] = Field(
        default_factory=list, description="Top drivers and context factors"
    )
    explanation: dict[str, Any] = Field(
        default_factory=dict, description="Structured non-judgmental explanation"
    )


class ExpenseForecaster:
    """Production expense forecasting engine using gradient boosted quantile regression.

    Predicts next-month total expense at quantiles:
    - 0.50: Median robust point forecast
    - 0.10: 10th percentile lower bound
    - 0.90: 90th percentile upper bound

    Fallback:
    When user history has < 3 months of activity or lag features are unavailable,
    falls back to a 3-month moving average (or available mean) with historical standard deviation.
    """

    FEATURE_NAMES = [
        "expense",
        "lag2_expense",
        "lag3_expense",
        "rolling_expense_3m_mean",
        "rolling_expense_3m_std",
        "spending_trend_3m",
        "income",
        "savings_rate",
        "necessity_rate",
        "discretionary_rate",
        "txn_count",
        "cashout_count",
        "target_month_num",
        "is_target_eid",
    ]

    def __init__(
        self,
        model_p50: HistGradientBoostingRegressor | None = None,
        model_p10: HistGradientBoostingRegressor | None = None,
        model_p90: HistGradientBoostingRegressor | None = None,
        feature_medians: dict[str, float] | None = None,
        model_version: str = "v1.0.0",
    ) -> None:
        self.model_p50 = model_p50
        self.model_p10 = model_p10
        self.model_p90 = model_p90
        self.feature_medians = feature_medians or {}
        self.model_version = model_version
        self.model_name = "expense_forecaster"
        self.is_fitted = model_p50 is not None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Fit quantile regressors for median (0.50), lower bound (0.08), and upper bound (0.92)."""
        # Fit median
        self.model_p50 = HistGradientBoostingRegressor(
            loss="quantile",
            quantile=0.50,
            max_iter=150,
            random_state=42,
        )
        self.model_p50.fit(X, y)

        # Fit lower bound (alpha = 0.08 for calibrated ~80% coverage)
        self.model_p10 = HistGradientBoostingRegressor(
            loss="quantile",
            quantile=0.08,
            max_iter=150,
            random_state=42,
        )
        self.model_p10.fit(X, y)

        # Fit upper bound (alpha = 0.92 for calibrated ~80% coverage)
        self.model_p90 = HistGradientBoostingRegressor(
            loss="quantile",
            quantile=0.92,
            max_iter=150,
            random_state=42,
        )
        self.model_p90.fit(X, y)

        self.is_fitted = True

    def predict(
        self,
        current_expense: float | Decimal,
        lag2_expense: float | Decimal | None = None,
        lag3_expense: float | Decimal | None = None,
        rolling_3m_mean: float | Decimal | None = None,
        rolling_3m_std: float | Decimal | None = None,
        spending_trend_3m: float | Decimal | None = None,
        income: float | Decimal | None = None,
        savings_rate: float | None = None,
        necessity_rate: float | None = None,
        discretionary_rate: float | None = None,
        txn_count: int = 25,
        cashout_count: int = 2,
        target_month_num: int = 4,
        target_month_str: str = "2026-04",
        history_months_count: int = 3,
    ) -> ForecastOutputContract:
        """Generate expense forecast with uncertainty intervals.

        Falls back to 3-month moving average if models are not fitted or history < 2 months.
        """
        curr_exp = max(0.0, float(current_expense))
        r_mean = float(rolling_3m_mean) if rolling_3m_mean is not None else curr_exp
        r_std = float(rolling_3m_std) if rolling_3m_std is not None else (0.15 * curr_exp)

        # Graceful fallback check
        if not self.is_fitted or history_months_count < 2 or self.model_p50 is None:
            return self._fallback_forecast(
                current_expense=curr_exp,
                rolling_3m_mean=r_mean,
                rolling_3m_std=r_std,
                target_month_str=target_month_str,
                target_month_num=target_month_num,
            )

        l2 = float(lag2_expense) if lag2_expense is not None else curr_exp
        l3 = float(lag3_expense) if lag3_expense is not None else l2
        trend = float(spending_trend_3m) if spending_trend_3m is not None else 0.0
        inc = float(income) if income is not None else (curr_exp * 1.2)
        sr = float(savings_rate) if savings_rate is not None else 0.15
        nr = float(necessity_rate) if necessity_rate is not None else 0.75
        dr = float(discretionary_rate) if discretionary_rate is not None else 0.15
        is_eid = 1.0 if target_month_num in (3, 5) else 0.0

        x_vec = np.array(
            [
                [
                    curr_exp,
                    l2,
                    l3,
                    r_mean,
                    r_std,
                    trend,
                    inc,
                    sr,
                    nr,
                    dr,
                    max(1, int(txn_count)),
                    max(0, int(cashout_count)),
                    target_month_num,
                    is_eid,
                ]
            ],
            dtype=np.float64,
        )

        p50 = float(self.model_p50.predict(x_vec)[0])
        p10 = float(self.model_p10.predict(x_vec)[0]) if self.model_p10 else (p50 * 0.80)
        p90 = float(self.model_p90.predict(x_vec)[0]) if self.model_p90 else (p50 * 1.20)

        # Enforce strict quantile monotonicity: p10 <= p50 <= p90
        p50 = max(0.0, p50)
        p10 = max(0.0, min(p10, p50))
        p90 = max(p50, p90)

        interval_width = p90 - p10

        # Build factors & non-judgmental explanation
        factors = self._build_factors(
            curr_exp=curr_exp,
            p50=p50,
            trend=trend,
            is_eid=bool(is_eid),
            dr=dr,
            target_month_num=target_month_num,
        )

        explanation = {
            "summary": (
                f"Projected next-month expense is approximately ৳{p50:,.2f} "
                f"(expected range: ৳{p10:,.2f} to ৳{p90:,.2f})."
            ),
            "tone": "descriptive",
            "drivers": [f["name"] for f in factors],
            "target_month": target_month_str,
        }

        return ForecastOutputContract(
            predicted_expense=round(p50, 2),
            lower_bound_p10=round(p10, 2),
            upper_bound_p90=round(p90, 2),
            prediction_interval_width=round(interval_width, 2),
            fallback_used=False,
            model_version=self.model_version,
            target_month=target_month_str,
            factors=factors,
            explanation=explanation,
        )

    def _fallback_forecast(
        self,
        current_expense: float,
        rolling_3m_mean: float,
        rolling_3m_std: float,
        target_month_str: str,
        target_month_num: int,
    ) -> ForecastOutputContract:
        """Deterministic 3-month moving average baseline fallback."""
        base = rolling_3m_mean if rolling_3m_mean > 0 else current_expense
        # Festival surge adjustment for Eid months
        mult = 1.25 if target_month_num in (3, 5) else 1.0
        predicted = base * mult

        spread = max(rolling_3m_std, 0.15 * predicted)
        p10 = max(0.0, predicted - 1.28 * spread)
        p90 = predicted + 1.28 * spread
        interval_width = p90 - p10

        factors = [
            {
                "name": "3-Month Moving Average",
                "impact": "Baseline",
                "description": f"Historical moving average spend of ৳{base:,.2f}",
            }
        ]
        if mult > 1.0:
            factors.append(
                {
                    "name": "Cultural Festival Calendar",
                    "impact": "Elevating",
                    "description": "Seasonal adjustment for festive month",
                }
            )

        explanation = {
            "summary": (
                f"Based on your recent 3-month average, next month's projected expense is "
                f"৳{predicted:,.2f} (estimated range: ৳{p10:,.2f} to ৳{p90:,.2f})."
            ),
            "tone": "descriptive",
            "drivers": ["3-month moving average"],
            "target_month": target_month_str,
        }

        return ForecastOutputContract(
            predicted_expense=round(predicted, 2),
            lower_bound_p10=round(p10, 2),
            upper_bound_p90=round(p90, 2),
            prediction_interval_width=round(interval_width, 2),
            fallback_used=True,
            model_version=self.model_version,
            target_month=target_month_str,
            factors=factors,
            explanation=explanation,
        )

    def _build_factors(
        self,
        curr_exp: float,
        p50: float,
        trend: float,
        is_eid: bool,
        dr: float,
        target_month_num: int,
    ) -> list[dict[str, Any]]:
        """Construct non-judgmental drivers and context factors."""
        factors: list[dict[str, Any]] = []

        if is_eid:
            factors.append(
                {
                    "name": "Cultural Festival Calendar",
                    "impact": "Elevating",
                    "description": "Expected festive spending volume for upcoming Eid holidays",
                }
            )

        if abs(trend) > 500.0:
            direction = "Upward" if trend > 0 else "Downward"
            factors.append(
                {
                    "name": f"{direction} Spending Momentum",
                    "impact": "Elevating" if trend > 0 else "Moderating",
                    "description": f"Recent 3-month spending momentum ({trend:+,.0f} BDT)",
                }
            )

        if dr > 0.25:
            factors.append(
                {
                    "name": "Discretionary Spending Ratio",
                    "impact": "Variable",
                    "description": f"Discretionary outlays constitute {dr * 100.0:.0f}% of regular budget",
                }
            )

        if not factors:
            factors.append(
                {
                    "name": "Baseline Consistency",
                    "impact": "Stable",
                    "description": "Consistent spending pattern across primary living categories",
                }
            )

        return factors

    def explain(self, inputs: Any) -> dict[str, Any]:
        """Explain protocol implementation."""
        if isinstance(inputs, dict):
            res = self.predict(**inputs)
            return res.explanation
        return {"summary": "Expense forecaster point and uncertainty prediction."}

    def save(self, filepath: str | Path, metadata_extra: dict[str, Any] | None = None) -> Path:
        """Serialize forecaster bundle with SHA-256 cryptographic digest."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        bundle = {
            "model_p50": self.model_p50,
            "model_p10": self.model_p10,
            "model_p90": self.model_p90,
            "feature_medians": self.feature_medians,
            "model_version": self.model_version,
        }
        joblib.dump(bundle, path, compress=3)

        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        digest = sha256.hexdigest()

        meta_path = path.parent / f"{path.stem}_metadata.json"
        metadata = {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "sha256_checksum": digest,
            "file_name": path.name,
            "file_size_bytes": path.stat().st_size,
            "saved_at": datetime.now(UTC).isoformat(),
            **(metadata_extra or {}),
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return path

    @classmethod
    def load(cls, filepath: str | Path, verify_checksum: bool = True) -> ExpenseForecaster:
        """Load serialized bundle with cryptographic tamper verification."""
        path = Path(filepath)
        meta_path = path.parent / f"{path.stem}_metadata.json"

        if verify_checksum:
            if not meta_path.exists():
                raise FileNotFoundError(f"Metadata manifest {meta_path} missing.")
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            expected_sha = meta.get("sha256_checksum")
            if not expected_sha:
                raise ValueError("Metadata missing sha256_checksum key.")

            sha256 = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(65536):
                    sha256.update(chunk)
            actual_sha = sha256.hexdigest()

            if actual_sha != expected_sha:
                raise PermissionError(
                    f"Cryptographic tamper verification FAILED for {path}! "
                    f"Expected {expected_sha}, got {actual_sha}."
                )

        bundle = joblib.load(path)
        return cls(
            model_p50=bundle["model_p50"],
            model_p10=bundle["model_p10"],
            model_p90=bundle["model_p90"],
            feature_medians=bundle.get("feature_medians", {}),
            model_version=bundle.get("model_version", "v1.0.0"),
        )
