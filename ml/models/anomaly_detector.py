"""Unified production anomaly detection engine for Sohoj.

Integrates transaction-level robust Z-score (median/MAD) and category-month
Isolation Forest detectors with alert budgeting, non-judgmental explanations,
and SHA-256 tamper verification.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

import joblib
from pydantic import BaseModel, ConfigDict, Field

from ml.models.category_month_anomaly import (
    CategoryMonthAnomalyDetector,
)
from ml.models.transaction_anomaly import (
    TransactionAnomalyDetector,
)


class AnomalyOutputContract(BaseModel):
    """Strict output contract required by Phase 9 specification.

    Fields:
        is_anomaly: Binary classification indicator.
        anomaly_score: Normalized anomaly severity [0.0, 1.0].
        observed: Actual observed amount in BDT.
        baseline: Expected baseline amount in BDT.
        deviation_pct: Percentage deviation from baseline.
        scope: Either 'transaction' or 'category_month'.
        explanation: Structured, non-judgmental factor breakdown.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    is_anomaly: bool = Field(..., description="Whether event is classified as anomalous")
    anomaly_score: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized anomaly confidence [0, 1]"
    )
    observed: float = Field(..., description="Observed transaction or monthly spend amount")
    baseline: float = Field(..., description="Expected baseline value")
    deviation_pct: float = Field(..., description="Percentage variance from baseline")
    scope: Literal["transaction", "category_month"] = Field(..., description="Scope of anomaly")
    category: str = Field(..., description="Associated spending category")
    budget_suppressed: bool = Field(
        default=False,
        description="True if anomaly was suppressed to preserve <= 3 alerts/user/month budget",
    )
    explanation: dict[str, Any] = Field(
        default_factory=dict, description="Structured non-judgmental explanation"
    )


class UnifiedAnomalyDetector:
    """Production unified anomaly detection engine.

    Combines:
    1. Transaction-level robust z-score (median/MAD) with peer-group fallback.
    2. Category-month Isolation Forest on multi-dimensional deviation features.
    3. Cultural festival context calibration (Dhaka 2026 calendar).
    4. Alert budgeting manager enforcing <= 3 alerts/user/month ceiling.
    """

    MAX_ALERTS_PER_USER_MONTH = 3

    FORBIDDEN_WORDS = {
        "bad",
        "awful",
        "terrible",
        "wasteful",
        "careless",
        "reckless",
        "irresponsible",
        "poor",
        "guilty",
        "sinful",
        "problematic",
    }

    def __init__(
        self,
        transaction_detector: TransactionAnomalyDetector | None = None,
        category_month_detector: CategoryMonthAnomalyDetector | None = None,
        model_version: str = "v1.0.0",
    ) -> None:
        self.transaction_detector = (
            transaction_detector
            if transaction_detector is not None
            else TransactionAnomalyDetector()
        )
        self.category_month_detector = (
            category_month_detector
            if category_month_detector is not None
            else CategoryMonthAnomalyDetector()
        )
        self.model_version = model_version

    def evaluate_transaction(
        self,
        amount: float | Decimal,
        category: str,
        user_id: str | None = None,
        txn_timestamp: datetime | str | None = None,
        occupation: str | None = None,
        festival_multiplier: float = 1.0,
        recent_txn_count_20m: int = 1,
    ) -> AnomalyOutputContract:
        """Evaluate a single transaction against user and peer baselines."""
        res = self.transaction_detector.detect(
            amount=amount,
            category=category,
            user_id=user_id,
            txn_timestamp=txn_timestamp,
            occupation=occupation,
            festival_multiplier=festival_multiplier,
            recent_txn_count_20m=recent_txn_count_20m,
        )

        self._validate_non_judgmental(res.explanation)

        return AnomalyOutputContract(
            is_anomaly=res.is_anomaly,
            anomaly_score=res.anomaly_score,
            observed=res.observed,
            baseline=res.baseline,
            deviation_pct=res.deviation_pct,
            scope="transaction",
            category=res.category,
            explanation=res.explanation,
        )

    def evaluate_category_month(
        self,
        amount: float | Decimal,
        category: str,
        category_share: float,
        txn_count: int,
        mean_day_of_month: float = 15.0,
        rolling_3m_avg: float | None = None,
        month: str = "2026-01",
        user_id: str | None = None,
    ) -> AnomalyOutputContract:
        """Evaluate a category-month spending aggregate."""
        res = self.category_month_detector.predict_record(
            amount=amount,
            category=category,
            category_share=category_share,
            txn_count=txn_count,
            mean_day_of_month=mean_day_of_month,
            rolling_3m_avg=rolling_3m_avg,
            month=month,
            user_id=user_id,
        )

        self._validate_non_judgmental(res.explanation)

        return AnomalyOutputContract(
            is_anomaly=res.is_anomaly,
            anomaly_score=res.anomaly_score,
            observed=res.observed,
            baseline=res.baseline,
            deviation_pct=res.deviation_pct,
            scope="category_month",
            category=res.category,
            explanation=res.explanation,
        )

    def apply_alert_budget(
        self,
        candidates: list[AnomalyOutputContract],
        max_alerts: int = MAX_ALERTS_PER_USER_MONTH,
    ) -> list[AnomalyOutputContract]:
        """Filter candidate anomalies for a user in a month to respect the alert budget.

        Ranks anomalies by anomaly_score descending.
        The top `max_alerts` remain active (is_anomaly=True).
        Any subsequent candidates have budget_suppressed=True and is_anomaly=False
        to prevent user fatigue while retaining audit visibility.
        """
        # Separate anomalies from non-anomalies
        anomalies = [c for c in candidates if c.is_anomaly]
        non_anomalies = [c for c in candidates if not c.is_anomaly]

        if len(anomalies) <= max_alerts:
            return candidates

        # Sort descending by score
        anomalies_sorted = sorted(anomalies, key=lambda x: x.anomaly_score, reverse=True)

        final_list: list[AnomalyOutputContract] = []
        for i, item in enumerate(anomalies_sorted):
            if i < max_alerts:
                final_list.append(item)
            else:
                # Suppress under alert budget
                suppressed = item.model_copy(
                    update={
                        "is_anomaly": False,
                        "budget_suppressed": True,
                    }
                )
                final_list.append(suppressed)

        final_list.extend(non_anomalies)
        return final_list

    def _validate_non_judgmental(self, explanation: dict[str, Any]) -> None:
        """Verify explanation string contains no derogatory or moralizing vocabulary."""
        text = str(explanation).lower()
        for forbidden in self.FORBIDDEN_WORDS:
            if f" {forbidden} " in f" {text} ":
                raise ValueError(
                    f"Violation of non-judgmental language contract: found '{forbidden}' in explanation"
                )

    def save(self, filepath: str | Path, metadata_extra: dict[str, Any] | None = None) -> Path:
        """Serialize model bundle with cryptographic SHA-256 checksum."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        bundle = {
            "transaction_detector": self.transaction_detector,
            "category_month_detector": self.category_month_detector,
            "model_version": self.model_version,
        }
        joblib.dump(bundle, path, compress=3)

        # Compute SHA-256
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        digest = sha256.hexdigest()

        metadata = {
            "model_version": self.model_version,
            "sha256_checksum": digest,
            "file_name": path.name,
            "file_size_bytes": path.stat().st_size,
            "saved_at": datetime.now(UTC).isoformat(),
            **(metadata_extra or {}),
        }

        meta_path = path.parent / f"{path.stem}_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return path

    @classmethod
    def load(cls, filepath: str | Path, verify_checksum: bool = True) -> UnifiedAnomalyDetector:
        """Load serialized bundle with cryptographic tamper-detection check."""
        path = Path(filepath)
        meta_path = path.parent / f"{path.stem}_metadata.json"

        if verify_checksum:
            if not meta_path.exists():
                raise FileNotFoundError(
                    f"Security manifest {meta_path} missing. Cannot verify model authenticity."
                )
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            expected_sha = meta.get("sha256_checksum")
            if not expected_sha:
                raise ValueError("Metadata manifest missing 'sha256_checksum' key.")

            sha256 = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(65536):
                    sha256.update(chunk)
            actual_sha = sha256.hexdigest()

            if actual_sha != expected_sha:
                raise PermissionError(
                    f"Cryptographic tamper check FAILED for {path}! "
                    f"Expected {expected_sha}, got {actual_sha}. Rejecting untrusted model."
                )

        bundle = joblib.load(path)
        detector = cls(
            transaction_detector=bundle["transaction_detector"],
            category_month_detector=bundle["category_month_detector"],
            model_version=bundle.get("model_version", "v1.0.0"),
        )
        return detector
