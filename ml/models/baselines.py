"""Rule-based statistical baselines for behavior classification, anomaly detection, and expense forecasting."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
import numpy as np


# =============================================================================
# 1. Behavior Classification Baseline (Threshold Rules)
# =============================================================================

@dataclass
class BehaviorPrediction:
    profile: str
    confidence: float
    top_factors: list[dict[str, Any]] = field(default_factory=list)
    is_cold_start: bool = False


class RuleBasedBehaviorClassifier:
    """Deterministic threshold-based behavioral persona classifier.

    Serves as the production baseline and cold-start fallback as specified in design.md §5.2.
    """

    def predict(
        self,
        savings_rate: float,
        cashout_ratio: float,
        cashout_count: float,
        necessity_share: float,
        discretionary_share: float,
        volatility_cv: float = 0.15,
        months_active: int = 12,
    ) -> BehaviorPrediction:
        """Classify user profile based on 3-month rolling aggregates."""
        # Cold start check (< 2 months of history)
        if months_active < 2:
            return BehaviorPrediction(
                profile="insufficient_data",
                confidence=0.0,
                top_factors=[{"feature": "months_active", "value": months_active, "status": "cold_start"}],
                is_cold_start=True,
            )

        # Rule evaluation hierarchy:
        # 1. Cash-dominant transactor
        if cashout_ratio >= 0.45 or cashout_count >= 3.5:
            return BehaviorPrediction(
                profile="cash_dominant_transactor",
                confidence=0.78,
                top_factors=[
                    {"feature": "cashout_ratio", "value": round(cashout_ratio, 2), "direction": "high"},
                    {"feature": "cashout_count", "value": round(cashout_count, 1), "direction": "high"},
                ],
            )

        # 2. Consistent saver
        if savings_rate >= 0.15 and necessity_share <= 0.85:
            return BehaviorPrediction(
                profile="consistent_saver",
                confidence=0.82,
                top_factors=[
                    {"feature": "savings_rate", "value": round(savings_rate, 2), "direction": "high"},
                    {"feature": "necessity_share", "value": round(necessity_share, 2), "direction": "moderate"},
                ],
            )

        # 3. Tight budgeter
        if necessity_share >= 0.78 and savings_rate < 0.10:
            return BehaviorPrediction(
                profile="tight_budgeter",
                confidence=0.80,
                top_factors=[
                    {"feature": "necessity_share", "value": round(necessity_share, 2), "direction": "high"},
                    {"feature": "savings_rate", "value": round(savings_rate, 2), "direction": "low"},
                ],
            )

        # 4. Discretionary spender
        if discretionary_share >= 0.22 or (discretionary_share > 0.18 and savings_rate < 0.05):
            return BehaviorPrediction(
                profile="discretionary_spender",
                confidence=0.75,
                top_factors=[
                    {"feature": "discretionary_share", "value": round(discretionary_share, 2), "direction": "high"},
                    {"feature": "savings_rate", "value": round(savings_rate, 2), "direction": "low"},
                ],
            )

        # 5. Volatile earner
        if volatility_cv >= 0.35:
            return BehaviorPrediction(
                profile="volatile_earner",
                confidence=0.72,
                top_factors=[
                    {"feature": "volatility_cv", "value": round(volatility_cv, 2), "direction": "high"}
                ],
            )

        # 6. Balanced spender (Default fallback)
        return BehaviorPrediction(
            profile="balanced_spender",
            confidence=0.65,
            top_factors=[
                {"feature": "savings_rate", "value": round(savings_rate, 2), "direction": "balanced"},
                {"feature": "necessity_share", "value": round(necessity_share, 2), "direction": "balanced"},
            ],
        )


# =============================================================================
# 2. Anomaly Detection Baseline (Robust Z-Score / MAD)
# =============================================================================

@dataclass
class AnomalyDetectionResult:
    is_anomaly: bool
    score: float
    observed: float
    baseline_median: float
    deviation_pct: float
    method: str = "robust_z_score_mad"
    fallback_used: bool = False


class RobustZScoreAnomalyDetector:
    """Transaction-level anomaly detector using Median and Median Absolute Deviation (MAD).

    Formula:
        MAD = median(|X - median(X)|)
        Modified Z = 0.6745 * (x - median(X)) / MAD
    Fallback: Uses peer-group statistics when user category history has < 10 transactions.
    """

    def __init__(self, z_threshold: float = 3.5, min_history_samples: int = 10) -> None:
        self.z_threshold = z_threshold
        self.min_history_samples = min_history_samples

    def detect(
        self,
        amount: float | Decimal,
        user_history: list[float] | np.ndarray,
        peer_median: float = 500.0,
        peer_mad: float = 200.0,
    ) -> AnomalyDetectionResult:
        """Evaluate if transaction amount is an anomaly against historical baseline."""
        amt_float = float(amount)
        hist = np.asarray(user_history, dtype=np.float64)

        fallback_used = False
        if len(hist) < self.min_history_samples:
            # Fallback to peer-group distribution
            med = peer_median
            mad = max(peer_mad, 1.0)
            fallback_used = True
        else:
            med = float(np.median(hist))
            abs_devs = np.abs(hist - med)
            mad = float(np.median(abs_devs))
            if mad < 1.0:
                # Minimum resolution threshold to prevent division by zero
                mad = max(float(np.mean(abs_devs)), 1.0)

        # Modified Z-Score (Boris Iglewicz and David Hoaglin 1993 standard)
        modified_z = (0.6745 * (amt_float - med)) / mad
        is_anomaly = bool(abs(modified_z) >= self.z_threshold)

        dev_pct = ((amt_float - med) / max(med, 1.0)) * 100.0

        return AnomalyDetectionResult(
            is_anomaly=is_anomaly,
            score=round(float(modified_z), 3),
            observed=round(amt_float, 2),
            baseline_median=round(med, 2),
            deviation_pct=round(dev_pct, 1),
            fallback_used=fallback_used,
        )


# =============================================================================
# 3. Expense Forecasting Baselines (Naive + 3-Month Moving Average)
# =============================================================================

@dataclass
class ForecastResult:
    forecast: float
    lower_bound: float
    upper_bound: float
    method: str
    historical_points_used: int


class ExpenseForecasterBaseline:
    """Deterministic forecasting baselines: Naive and 3-Month Moving Average.

    Serves as the benchmark for gradient boosted trees in Phase 3 as specified in design.md §5.4.
    """

    def predict_naive(self, history: list[float] | np.ndarray) -> ForecastResult:
        """Naive forecast: Next month equals last observed month."""
        h = np.asarray(history, dtype=np.float64)
        if len(h) == 0:
            return ForecastResult(forecast=0.0, lower_bound=0.0, upper_bound=0.0, method="naive", historical_points_used=0)

        last_val = float(h[-1])
        # Simple heuristic bounds (+/- 25%)
        lower = max(0.0, last_val * 0.75)
        upper = last_val * 1.25

        return ForecastResult(
            forecast=round(last_val, 2),
            lower_bound=round(lower, 2),
            upper_bound=round(upper, 2),
            method="naive",
            historical_points_used=1,
        )

    def predict_moving_average(
        self, history: list[float] | np.ndarray, window: int = 3
    ) -> ForecastResult:
        """3-Month Simple Moving Average forecast with standard error bounds."""
        h = np.asarray(history, dtype=np.float64)
        if len(h) == 0:
            return ForecastResult(forecast=0.0, lower_bound=0.0, upper_bound=0.0, method="sma_3m", historical_points_used=0)

        pts = min(len(h), window)
        window_slice = h[-pts:]
        pred = float(np.mean(window_slice))
        std = float(np.std(window_slice)) if pts > 1 else pred * 0.15

        lower = max(0.0, pred - 1.645 * std)  # 90% confidence approx
        upper = pred + 1.645 * std

        return ForecastResult(
            forecast=round(pred, 2),
            lower_bound=round(lower, 2),
            upper_bound=round(upper, 2),
            method=f"sma_{pts}m",
            historical_points_used=pts,
        )
