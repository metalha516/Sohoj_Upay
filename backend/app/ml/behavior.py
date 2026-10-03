"""Backend adapter for Model A (Behavior Classification).

Exposes the BehaviorClassifier singleton for use by FastAPI services,
asynchronous workers, and coaching agents.
"""

from __future__ import annotations

from pathlib import Path

from ml.models.behavior_classifier import (
    BehaviorClassifier,
    BehaviorPrediction,
    SecurityError,
)

_MODEL_INSTANCE: BehaviorClassifier | None = None


def get_behavior_classifier() -> BehaviorClassifier:
    """Retrieve or lazily initialize verified BehaviorClassifier singleton."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        model_path = Path("ml/artifacts/behavior_classifier_v1.joblib")
        meta_path = Path("ml/artifacts/behavior_classifier_v1_metadata.json")

        if not model_path.exists():
            raise FileNotFoundError(
                f"Trained BehaviorClassifier artifact not found at {model_path}. "
                "Ensure training pipeline has been executed."
            )

        _MODEL_INSTANCE = BehaviorClassifier.load(model_path, meta_path)

    return _MODEL_INSTANCE


__all__ = [
    "BehaviorClassifier",
    "BehaviorPrediction",
    "SecurityError",
    "get_behavior_classifier",
]
