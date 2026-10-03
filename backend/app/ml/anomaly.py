"""Backend adapter for Model B (Anomaly Detection).

Exposes the verified UnifiedAnomalyDetector singleton for use by FastAPI services,
asynchronous transaction workers, and coaching agents.
"""

from __future__ import annotations

from pathlib import Path

from ml.models.anomaly_detector import (
    AnomalyOutputContract,
    UnifiedAnomalyDetector,
)

_DETECTOR_INSTANCE: UnifiedAnomalyDetector | None = None


def get_anomaly_detector() -> UnifiedAnomalyDetector:
    """Retrieve or lazily initialize verified UnifiedAnomalyDetector singleton."""
    global _DETECTOR_INSTANCE
    if _DETECTOR_INSTANCE is None:
        model_path = Path("ml/artifacts/anomaly_detector_v1.joblib")

        if not model_path.exists():
            raise FileNotFoundError(
                f"Trained UnifiedAnomalyDetector artifact not found at {model_path}. "
                "Ensure training pipeline (train_anomaly_detector.py) has been executed."
            )

        _DETECTOR_INSTANCE = UnifiedAnomalyDetector.load(model_path, verify_checksum=True)

    return _DETECTOR_INSTANCE


def reset_anomaly_detector() -> None:
    """Reset the singleton instance (primarily for testing)."""
    global _DETECTOR_INSTANCE
    _DETECTOR_INSTANCE = None


__all__ = [
    "AnomalyOutputContract",
    "UnifiedAnomalyDetector",
    "get_anomaly_detector",
    "reset_anomaly_detector",
]
