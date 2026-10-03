"""Anomaly analyst feedback service for recording and threshold tuning.

Supports analyst and user feedback actions ('confirmed' / 'dismissed'),
tracks false-positive proxies, and calculates adaptive threshold offsets.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal


@dataclass
class AnomalyFeedbackRecord:
    """Feedback entry recorded for an anomaly."""

    feedback_id: uuid.UUID
    anomaly_id: uuid.UUID
    user_id: uuid.UUID
    category: str
    previous_status: str
    new_status: Literal["confirmed", "dismissed"]
    reviewer_role: Literal["user", "analyst", "system"]
    notes: str | None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FeedbackMetricsSummary:
    """Statistical summary of anomaly feedback."""

    total_reviewed: int
    confirmed_count: int
    dismissed_count: int
    confirmation_rate: float  # Precision proxy
    dismissal_rate: float  # False Positive proxy
    category_breakdown: dict[str, dict[str, float]]


class AnomalyFeedbackService:
    """Manages analyst and user feedback on detected anomalies.

    Enables:
    1. Feedback persistence ('confirmed' vs 'dismissed').
    2. Precision and False Positive Rate proxy monitoring.
    3. Adaptive threshold tuning per user/category based on dismissal rates.
    """

    def __init__(self) -> None:
        # In-memory storage for feedback events
        self._feedback_log: list[AnomalyFeedbackRecord] = []
        # Anomaly statuses: anomaly_id -> status
        self._status_registry: dict[uuid.UUID, str] = {}

    def record_feedback(
        self,
        anomaly_id: uuid.UUID,
        user_id: uuid.UUID,
        category: str,
        status: Literal["confirmed", "dismissed"],
        reviewer_role: Literal["user", "analyst", "system"] = "analyst",
        notes: str | None = None,
    ) -> AnomalyFeedbackRecord:
        """Record analyst or user feedback for an anomaly."""
        if status not in ("confirmed", "dismissed"):
            raise ValueError(
                f"Invalid feedback status '{status}'. Must be 'confirmed' or 'dismissed'."
            )

        prev_status = self._status_registry.get(anomaly_id, "open")
        self._status_registry[anomaly_id] = status

        record = AnomalyFeedbackRecord(
            feedback_id=uuid.uuid4(),
            anomaly_id=anomaly_id,
            user_id=user_id,
            category=category,
            previous_status=prev_status,
            new_status=status,
            reviewer_role=reviewer_role,
            notes=notes,
        )
        self._feedback_log.append(record)
        return record

    def get_status(self, anomaly_id: uuid.UUID) -> str:
        """Get the current review status of an anomaly."""
        return self._status_registry.get(anomaly_id, "open")

    def get_feedback_metrics(
        self,
        user_id: uuid.UUID | None = None,
    ) -> FeedbackMetricsSummary:
        """Compute feedback precision/dismissal metrics."""
        entries = (
            [e for e in self._feedback_log if e.user_id == user_id]
            if user_id is not None
            else self._feedback_log
        )

        total = len(entries)
        if total == 0:
            return FeedbackMetricsSummary(
                total_reviewed=0,
                confirmed_count=0,
                dismissed_count=0,
                confirmation_rate=0.0,
                dismissal_rate=0.0,
                category_breakdown={},
            )

        confirmed = sum(1 for e in entries if e.new_status == "confirmed")
        dismissed = sum(1 for e in entries if e.new_status == "dismissed")

        cat_breakdown: dict[str, dict[str, float]] = {}
        # Group by category
        categories = {e.category for e in entries}
        for cat in categories:
            cat_entries = [e for e in entries if e.category == cat]
            c_cnt = sum(1 for e in cat_entries if e.new_status == "confirmed")
            d_cnt = sum(1 for e in cat_entries if e.new_status == "dismissed")
            tot = len(cat_entries)
            cat_breakdown[cat] = {
                "total": float(tot),
                "confirmed": float(c_cnt),
                "dismissed": float(d_cnt),
                "dismissal_rate": round(d_cnt / tot, 4) if tot > 0 else 0.0,
            }

        return FeedbackMetricsSummary(
            total_reviewed=total,
            confirmed_count=confirmed,
            dismissed_count=dismissed,
            confirmation_rate=round(confirmed / total, 4),
            dismissal_rate=round(dismissed / total, 4),
            category_breakdown=cat_breakdown,
        )

    def compute_adaptive_threshold_offset(
        self,
        user_id: uuid.UUID,
        category: str,
        base_z_threshold: float = 3.5,
    ) -> float:
        """Calculate dynamic Z-score threshold adjusted for user dismissal history.

        If a user frequently dismisses alerts in this category (e.g. dismissal rate > 50%),
        the threshold is increased by up to +1.5 sigma to suppress future false alarms.
        If confirmed, the threshold remains sensitive.
        """
        user_cat_feedback = [
            e for e in self._feedback_log if e.user_id == user_id and e.category == category
        ]

        if len(user_cat_feedback) < 3:
            # Insufficient feedback history; use default
            return base_z_threshold

        dismissals = sum(1 for e in user_cat_feedback if e.new_status == "dismissed")
        dismissal_rate = dismissals / len(user_cat_feedback)

        if dismissal_rate > 0.60:
            # Significant false positive history for this category -> relax threshold
            offset = 1.0 * dismissal_rate
            return round(base_z_threshold + offset, 2)
        elif dismissal_rate < 0.20:
            # High confirmation rate -> keep sharp sensitivity
            return round(base_z_threshold - 0.2, 2)

        return base_z_threshold
