"""Category-month spending anomaly detector using Isolation Forest and LOF comparison.

Evaluates multi-transaction compositional and surge anomalies across (user, month, category).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler


@dataclass
class CategoryMonthAnomalyResult:
    """Standardized result for category-month anomaly detection."""

    is_anomaly: bool
    anomaly_score: float  # Normalized to [0.0, 1.0]
    observed: float  # Monthly category spend
    baseline: float  # Expected 3-month rolling mean or category baseline
    deviation_pct: float
    scope: Literal["category_month"] = "category_month"
    category: str = "other"
    user_id: str | None = None
    month: str | None = None
    category_share: float = 0.0
    txn_count: int = 0
    model_type: str = "isolation_forest"
    explanation: dict[str, Any] = field(default_factory=dict)


class CategoryMonthAnomalyDetector:
    """Category-month spending anomaly detector.

    Features extracted per (user, month, category):
    1. `amount`: Total BDT spent in this category during the month.
    2. `category_share`: Share of this category relative to user's total monthly spend.
    3. `txn_count`: Number of transactions in this category during the month.
    4. `mean_day_of_month`: Average day of month (1 to 31) when transactions occurred.
    5. `dev_vs_3m`: Ratio of current month spend to the 3-month rolling average for this category.
    6. `is_festival_month`: Binary flag indicating major cultural festival period (Eid / Boishakh).
    7. `expected_festival_multiplier`: Category-specific multiplier expected for festival context.
    """

    FEATURE_NAMES = [
        "amount",
        "category_share",
        "txn_count",
        "mean_day_of_month",
        "dev_vs_3m",
        "is_festival_month",
        "expected_festival_multiplier",
    ]

    def __init__(
        self,
        contamination: float = 0.03,
        random_state: int = 42,
    ) -> None:
        self.contamination = contamination
        self.random_state = random_state

        self.scaler = RobustScaler()
        self.isolation_forest: IsolationForest | None = None
        self.lof: LocalOutlierFactor | None = None
        self.active_model_name: str = "isolation_forest"
        self.is_fitted: bool = False

    @staticmethod
    def extract_features(
        transactions_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Aggregate transactions into (user, month, category) feature vectors."""
        df = transactions_df.copy()
        outflow = df[df["txn_type"].isin(["expense", "cash_out"])].copy()

        outflow["ts_dt"] = pd.to_datetime(outflow["ts"])
        outflow["month"] = outflow["ts_dt"].dt.strftime("%Y-%m")
        outflow["day"] = outflow["ts_dt"].dt.day

        # Total monthly outflow per user
        user_monthly_totals = (
            outflow.groupby(["user_id", "month"])["amount"]
            .sum()
            .reset_index()
            .rename(columns={"amount": "total_month_spend"})
        )

        # Aggregate per user, month, category
        cat_agg = (
            outflow.groupby(["user_id", "month", "category"])
            .agg(
                amount=("amount", "sum"),
                txn_count=("id", "count"),
                mean_day_of_month=("day", "mean"),
            )
            .reset_index()
        )

        merged = cat_agg.merge(user_monthly_totals, on=["user_id", "month"], how="left")
        merged["category_share"] = (
            merged["amount"] / np.maximum(merged["total_month_spend"], 1.0)
        ).clip(0.0, 1.0)

        # Sort chronologically to compute 3-month rolling average per user-category
        merged = merged.sort_values(["user_id", "category", "month"]).reset_index(drop=True)

        # Rolling 3-month lag average (excluding current month)
        merged["rolling_3m_avg"] = (
            merged.groupby(["user_id", "category"])["amount"]
            .shift(1)
            .rolling(3, min_periods=1)
            .mean()
        )
        merged["rolling_3m_avg"] = merged["rolling_3m_avg"].fillna(merged["amount"])

        # Deviation vs 3m average
        merged["dev_vs_3m"] = (
            (merged["amount"] - merged["rolling_3m_avg"])
            / np.maximum(merged["rolling_3m_avg"], 100.0)
        ).clip(-2.0, 15.0)

        # Festival context features for Bangladesh 2026:
        # Ramadan / Eid-ul-Fitr (March: 2026-03)
        # Pohela Boishakh (April: 2026-04)
        # Eid-ul-Adha (May: 2026-05)
        merged["is_festival_month"] = (
            merged["month"].isin(["2026-03", "2026-04", "2026-05"]).astype(float)
        )

        # Expected multiplier by category in festival months
        def _get_festival_mult(row: pd.Series) -> float:
            m = row["month"]
            cat = row["category"]
            if m == "2026-03":  # Eid-ul-Fitr
                if cat in ("shopping", "clothing"):
                    return 3.2
                if cat in ("travel", "transport"):
                    return 2.2
                if cat in ("groceries", "bazaar"):
                    return 1.35
            elif m == "2026-04":  # Pohela Boishakh
                if cat in ("dining", "entertainment", "shopping"):
                    return 1.8
            elif m == "2026-05":  # Eid-ul-Adha
                if cat in ("cash_out", "livestock"):
                    return 2.8
                if cat in ("travel", "transport"):
                    return 2.0
            return 1.0

        merged["expected_festival_multiplier"] = merged.apply(_get_festival_mult, axis=1)

        return merged

    def fit(self, features_df: pd.DataFrame) -> dict[str, Any]:
        """Fit both Isolation Forest and LOF, benchmark them, and set the active detector."""
        X_raw = features_df[self.FEATURE_NAMES].to_numpy(dtype=np.float64)
        # Impute NaNs with median
        col_medians = np.nanmedian(X_raw, axis=0)
        inds = np.where(np.isnan(X_raw))
        X_raw[inds] = np.take(col_medians, inds[1])

        X_scaled = self.scaler.fit_transform(X_raw)

        # 1. Fit Isolation Forest
        self.isolation_forest = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.isolation_forest.fit(X_scaled)

        # 2. Fit LOF in novelty detection mode
        self.lof = LocalOutlierFactor(
            n_neighbors=20,
            contamination=self.contamination,
            novelty=True,
            n_jobs=-1,
        )
        self.lof.fit(X_scaled)

        self.is_fitted = True

        # Generate comparison summary
        if_scores = -self.isolation_forest.score_samples(X_scaled)  # higher = more anomalous
        lof_scores = -self.lof.score_samples(X_scaled)

        if_preds = self.isolation_forest.predict(X_scaled) == -1
        lof_preds = self.lof.predict(X_scaled) == -1

        summary = {
            "n_samples": len(features_df),
            "if_anomaly_count": int(if_preds.sum()),
            "if_anomaly_pct": float(if_preds.mean() * 100.0),
            "lof_anomaly_count": int(lof_preds.sum()),
            "lof_anomaly_pct": float(lof_preds.mean() * 100.0),
            "concordance": float((if_preds == lof_preds).mean() * 100.0),
            "if_mean_score": float(np.mean(if_scores)),
            "lof_mean_score": float(np.mean(lof_scores)),
        }
        return summary

    def predict_record(
        self,
        amount: float | Decimal,
        category: str,
        category_share: float,
        txn_count: int,
        mean_day_of_month: float = 15.0,
        rolling_3m_avg: float | None = None,
        month: str = "2026-01",
        user_id: str | None = None,
        use_model: Literal["isolation_forest", "lof"] = "isolation_forest",
    ) -> CategoryMonthAnomalyResult:
        """Predict whether a single category-month record is anomalous."""
        amt_float = max(0.0, float(amount))
        base_3m = amt_float if rolling_3m_avg is None else max(100.0, float(rolling_3m_avg))
        dev_vs_3m = (amt_float - base_3m) / base_3m
        dev_pct = dev_vs_3m * 100.0

        is_fest = 1.0 if month in ["2026-03", "2026-04", "2026-05"] else 0.0

        # Calculate expected festival multiplier
        fest_mult = 1.0
        if month == "2026-03" and category in ("shopping", "travel"):
            fest_mult = 3.0
        elif month == "2026-04" and category in ("dining", "entertainment"):
            fest_mult = 1.8
        elif month == "2026-05" and category in ("cash_out", "travel"):
            fest_mult = 2.8

        x_row = np.array(
            [
                [
                    amt_float,
                    min(1.0, max(0.0, float(category_share))),
                    max(1, int(txn_count)),
                    max(1.0, min(31.0, float(mean_day_of_month))),
                    max(-2.0, min(15.0, float(dev_vs_3m))),
                    is_fest,
                    fest_mult,
                ]
            ],
            dtype=np.float64,
        )

        if not self.is_fitted or self.isolation_forest is None:
            # Fallback heuristic if not yet fitted
            is_anomaly = bool(dev_vs_3m >= 2.5 and amt_float >= 3000.0)
            score = min(1.0, max(0.0, dev_vs_3m / 5.0))
        else:
            x_scaled = self.scaler.transform(x_row)
            if use_model == "lof" and self.lof is not None:
                pred = self.lof.predict(x_scaled)[0]
                raw_score = -float(self.lof.score_samples(x_scaled)[0])
                # Normalize LOF score (baseline ~ 1.0)
                score = min(1.0, max(0.0, (raw_score - 1.0) / 2.0))
            else:
                pred = self.isolation_forest.predict(x_scaled)[0]
                raw_score = -float(self.isolation_forest.score_samples(x_scaled)[0])
                # IF score_samples ranges ~ [-0.8, -0.2], so -score_samples ranges [0.2, 0.8]
                score = min(1.0, max(0.0, (raw_score - 0.45) / 0.35))

            is_anomaly = bool(pred == -1)

        # Build non-judgmental explanation
        reasons: list[str] = []
        if dev_pct > 100.0:
            reasons.append(
                f"Monthly {category} spend is {amt_float / max(base_3m, 1.0):.1f}x higher than 3-month baseline"
            )
        if category_share > 0.40:
            reasons.append(
                f"Category accounts for {category_share * 100.0:.0f}% of total monthly expense"
            )

        if not reasons:
            summary = (
                f"Monthly spending of ৳{amt_float:,.2f} in {category} is within expected patterns."
            )
        else:
            summary = f"Elevated monthly spend in {category}: " + "; ".join(reasons) + "."

        explanation = {
            "summary": summary,
            "tone": "descriptive",
            "factors": [
                {
                    "factor": "monthly_amount",
                    "value": f"৳{amt_float:,.2f}",
                    "description": "Total spent in category this month",
                },
                {
                    "factor": "category_share",
                    "value": f"{category_share * 100.0:.1f}%",
                    "description": "Share of total monthly outflow",
                },
                {
                    "factor": "3m_baseline",
                    "value": f"৳{base_3m:,.2f}",
                    "description": "3-month rolling baseline for this category",
                },
                {
                    "factor": "deviation_pct",
                    "value": f"{dev_pct:+.1f}%",
                    "description": "Deviation from recent monthly average",
                },
            ],
            "month": month,
            "category": category,
        }

        return CategoryMonthAnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=round(score, 4),
            observed=round(amt_float, 2),
            baseline=round(base_3m, 2),
            deviation_pct=round(dev_pct, 2),
            scope="category_month",
            category=category,
            user_id=user_id,
            month=month,
            category_share=round(category_share, 4),
            txn_count=int(txn_count),
            model_type=use_model,
            explanation=explanation,
        )
