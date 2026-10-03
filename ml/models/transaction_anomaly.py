"""Transaction-level anomaly detection using robust z-score (median/MAD),

peer-group fallback, and festival-aware baseline calibration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

import numpy as np
import pandas as pd


@dataclass
class TransactionAnomalyResult:
    """Standardized result for single transaction anomaly detection."""

    is_anomaly: bool
    anomaly_score: float  # Normalized to [0.0, 1.0]
    observed: float
    baseline: float
    deviation_pct: float
    scope: Literal["transaction"] = "transaction"
    category: str = "other"
    fallback_used: bool = False
    peer_group_size: int = 0
    festival_adjusted: bool = False
    festival_multiplier: float = 1.0
    anomaly_reasons: list[str] = field(default_factory=list)
    explanation: dict[str, Any] = field(default_factory=dict)


class TransactionAnomalyDetector:
    """Robust Z-Score (median/MAD) anomaly detector for individual transactions.

    Formula:
        MAD = median(|X - median(X)|)
        Modified Z = 0.6745 * (amount - median) / max(MAD, min_mad)

    Peer-Group Fallback:
        When a user has < min_history_samples (default: 20) transactions in a category,
        the detector falls back to peer-group (population-wide category) statistics
        guaranteed to have >= 20 samples.

    Festival Calibration:
        During festival periods (e.g. Eid-ul-Fitr, Eid-ul-Adha, Pohela Boishakh),
        baselines are dynamically scaled by cultural spending multipliers to prevent
        excessive false positives on legitimate festive purchases.
    """

    def __init__(
        self,
        z_threshold: float = 3.5,
        min_history_samples: int = 20,
        odd_hour_start: int = 2,
        odd_hour_end: int = 4,
        burst_time_window_minutes: int = 20,
    ) -> None:
        self.z_threshold = z_threshold
        self.min_history_samples = min_history_samples
        self.odd_hour_start = odd_hour_start
        self.odd_hour_end = odd_hour_end
        self.burst_time_window_minutes = burst_time_window_minutes

        # Cached baselines: (user_id, category) -> (median, mad, count)
        self.user_baselines: dict[tuple[str, str], tuple[float, float, int]] = {}
        # Global category baselines: category -> (median, mad, count)
        self.global_baselines: dict[str, tuple[float, float, int]] = {}
        # Occupation category baselines: (occupation, category) -> (median, mad, count)
        self.peer_baselines: dict[tuple[str, str], tuple[float, float, int]] = {}

    def fit_from_dataframe(
        self,
        transactions_df: pd.DataFrame,
        users_df: pd.DataFrame | None = None,
    ) -> None:
        """Compute user, peer, and global category baseline distributions."""
        df = transactions_df.copy()
        if "amount" not in df.columns or "category" not in df.columns:
            raise ValueError("transactions_df must contain 'amount' and 'category' columns")

        # Restrict baselines to outflow transactions (expense & cash_out)
        if "txn_type" in df.columns:
            outflows = df[df["txn_type"].isin(["expense", "cash_out"])].copy()
        else:
            outflows = df.copy()

        # 1. Global category baselines
        self.global_baselines = {}
        for cat, grp in outflows.groupby("category"):
            amt = grp["amount"].to_numpy(dtype=np.float64)
            med = float(np.median(amt))
            mad = float(np.median(np.abs(amt - med)))
            safe_mad = max(mad, 1.0, 0.05 * med)
            self.global_baselines[str(cat)] = (med, safe_mad, len(amt))

        # 2. User-category baselines
        self.user_baselines = {}
        if "user_id" in outflows.columns:
            for (uid, cat), grp in outflows.groupby(["user_id", "category"]):
                amt = grp["amount"].to_numpy(dtype=np.float64)
                med = float(np.median(amt))
                mad = float(np.median(np.abs(amt - med)))
                safe_mad = max(mad, 1.0, 0.05 * med)
                self.user_baselines[(str(uid), str(cat))] = (med, safe_mad, len(amt))

        # 3. Peer-group baselines (e.g. occupation-category if available)
        self.peer_baselines = {}
        if (
            users_df is not None
            and "occupation" in users_df.columns
            and "user_id" in outflows.columns
        ):
            occ_map = users_df.set_index("id")["occupation"].to_dict()
            outflows["occupation"] = outflows["user_id"].map(occ_map)
            for (occ, cat), grp in outflows.groupby(["occupation", "category"]):
                if pd.notna(occ):
                    amt = grp["amount"].to_numpy(dtype=np.float64)
                    med = float(np.median(amt))
                    mad = float(np.median(np.abs(amt - med)))
                    safe_mad = max(mad, 1.0, 0.05 * med)
                    self.peer_baselines[(str(occ), str(cat))] = (med, safe_mad, len(amt))

    def get_baseline(
        self,
        user_id: str | None,
        category: str,
        occupation: str | None = None,
    ) -> tuple[float, float, int, bool]:
        """Retrieve baseline (median, mad, count, fallback_used).

        Guarantees minimum peer group size >= 20.
        """
        # 1. Try user history if user has sufficient history (>= min_history_samples)
        if user_id is not None and (user_id, category) in self.user_baselines:
            med, mad, cnt = self.user_baselines[(user_id, category)]
            if cnt >= self.min_history_samples:
                return med, mad, cnt, False

        # 2. Try peer-group (occupation + category) if available and group size >= min_history_samples
        if occupation is not None and (occupation, category) in self.peer_baselines:
            med, mad, cnt = self.peer_baselines[(occupation, category)]
            if cnt >= self.min_history_samples:
                return med, mad, cnt, True

        # 3. Fallback to global population category baseline
        if category in self.global_baselines:
            med, mad, cnt = self.global_baselines[category]
            return med, mad, cnt, True

        # 4. Ultimate cold-start default for unknown novel category
        default_med = 500.0
        default_mad = 250.0
        return default_med, default_mad, 20, True

    def detect(
        self,
        amount: float | Decimal,
        category: str,
        user_id: str | None = None,
        txn_timestamp: datetime | str | None = None,
        occupation: str | None = None,
        festival_multiplier: float = 1.0,
        recent_txn_count_20m: int = 1,
    ) -> TransactionAnomalyResult:
        """Evaluate whether a transaction is an anomaly.

        Args:
            amount: Transaction amount in BDT.
            category: Expense or cash-out category.
            user_id: User identifier (for personalized baseline).
            txn_timestamp: ISO timestamp or datetime object.
            occupation: Optional occupation segment for peer fallback.
            festival_multiplier: Seasonal multiplier (e.g., 3.2 for Eid shopping).
            recent_txn_count_20m: Number of transactions in the last 20 minutes (for burst check).

        Returns:
            TransactionAnomalyResult matching the required output contract.
        """
        amt_float = max(0.0, float(amount))

        # Retrieve baseline with peer fallback
        med, mad, cnt, fallback_used = self.get_baseline(user_id, category, occupation)

        # Apply festival adjustment if in a festive window
        festival_adjusted = False
        adj_mult = max(1.0, float(festival_multiplier))
        if adj_mult > 1.0:
            festival_adjusted = True
            baseline_med = med * adj_mult
            baseline_mad = mad * adj_mult
        else:
            baseline_med = med
            baseline_mad = mad

        safe_mad = max(baseline_mad, 1.0, 0.05 * max(baseline_med, 1.0))

        # Modified Z-Score calculation
        modified_z = (0.6745 * (amt_float - baseline_med)) / safe_mad
        deviation_pct = (
            ((amt_float - baseline_med) / max(baseline_med, 1.0)) * 100.0
            if baseline_med > 0
            else 0.0
        )

        anomaly_reasons: list[str] = []
        is_amount_anomaly = modified_z >= self.z_threshold

        # Normalized amount score via sigmoid centered around threshold
        # When mod_z == z_threshold, score is 0.50; when mod_z >> z_threshold, score -> 1.0
        z_diff = modified_z - self.z_threshold
        amount_score = 1.0 / (1.0 + math.exp(-max(-10.0, min(10.0, z_diff))))

        if is_amount_anomaly:
            times = amt_float / max(baseline_med, 1.0)
            anomaly_reasons.append(
                f"Amount ৳{amt_float:,.2f} is {times:.1f}x higher than baseline (৳{baseline_med:,.2f})"
            )

        # Check for odd-hour activity (Dhaka nighttime 02:00 - 04:30 AM)
        is_odd_hour = False
        odd_hour_score = 0.0
        if txn_timestamp is not None:
            if isinstance(txn_timestamp, str):
                try:
                    dt = datetime.fromisoformat(txn_timestamp)
                except ValueError:
                    dt = None
            else:
                dt = txn_timestamp

            if (
                dt is not None
                and self.odd_hour_start <= dt.hour <= self.odd_hour_end
                and amt_float >= 100.0
            ):
                is_odd_hour = True
                odd_hour_score = 0.85
                anomaly_reasons.append(
                    f"Transaction occurred during unusual hours ({dt.strftime('%I:%M %p')})"
                )

        # Check for rapid micro-transaction burst frequency (>= 3 txns within 20 mins)
        is_burst = False
        burst_score = 0.0
        if recent_txn_count_20m >= 3:
            is_burst = True
            burst_score = min(0.95, 0.60 + 0.10 * (recent_txn_count_20m - 2))
            anomaly_reasons.append(
                f"High-frequency burst of {recent_txn_count_20m} transactions within 20 minutes"
            )

        # Unified anomaly decision and score
        is_anomaly = is_amount_anomaly or is_odd_hour or is_burst

        # Overall anomaly score: max or blended score across components
        overall_score = max(
            amount_score if is_amount_anomaly else 0.10,
            odd_hour_score if is_odd_hour else 0.0,
            burst_score if is_burst else 0.0,
        )
        overall_score = max(0.0, min(1.0, round(overall_score, 4)))

        # Construct non-judgmental explanation
        explanation = self._build_explanation(
            amt=amt_float,
            category=category,
            baseline=baseline_med,
            deviation_pct=deviation_pct,
            reasons=anomaly_reasons,
            fallback_used=fallback_used,
            festival_adjusted=festival_adjusted,
            adj_mult=adj_mult,
        )

        return TransactionAnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=overall_score,
            observed=round(amt_float, 2),
            baseline=round(baseline_med, 2),
            deviation_pct=round(deviation_pct, 2),
            scope="transaction",
            category=category,
            fallback_used=fallback_used,
            peer_group_size=cnt,
            festival_adjusted=festival_adjusted,
            festival_multiplier=adj_mult,
            anomaly_reasons=anomaly_reasons,
            explanation=explanation,
        )

    def _build_explanation(
        self,
        amt: float,
        category: str,
        baseline: float,
        deviation_pct: float,
        reasons: list[str],
        fallback_used: bool,
        festival_adjusted: bool,
        adj_mult: float,
    ) -> dict[str, Any]:
        """Construct descriptive, non-judgmental explanation."""
        if not reasons:
            summary = (
                f"Transaction of ৳{amt:,.2f} in {category} is consistent with your typical pattern "
                f"(baseline: ৳{baseline:,.2f})."
            )
        else:
            summary = f"Unusual activity detected in {category}: " + "; ".join(reasons) + "."

        factors = [
            {
                "factor": "observed_amount",
                "value": f"৳{amt:,.2f}",
                "description": "Observed transaction amount",
            },
            {
                "factor": "baseline_median",
                "value": f"৳{baseline:,.2f}",
                "description": "Typical median amount for this category",
            },
            {
                "factor": "deviation_pct",
                "value": f"{deviation_pct:+.1f}%",
                "description": "Percentage variance from baseline",
            },
        ]

        if fallback_used:
            factors.append(
                {
                    "factor": "baseline_source",
                    "value": "peer_group",
                    "description": "Insufficient personal transaction history (< 20); used peer-group baseline",
                }
            )

        if festival_adjusted:
            factors.append(
                {
                    "factor": "seasonal_calibration",
                    "value": f"{adj_mult:.1f}x",
                    "description": "Baseline elevated for festive season",
                }
            )

        return {
            "summary": summary,
            "tone": "descriptive",
            "factors": factors,
            "category": category,
        }
