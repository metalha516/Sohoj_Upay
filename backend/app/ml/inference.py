"""Unified ML model serving layer for Sohoj.

Defines the common MLModel protocol, hot-reloadable singleton manager,
and graceful fallback to baseline upon missing or corrupt artifacts.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from ml.models.anomaly_detector import AnomalyOutputContract, UnifiedAnomalyDetector
from ml.models.baselines import RuleBasedBehaviorClassifier
from ml.models.behavior_classifier import BehaviorClassifier, BehaviorPrediction
from ml.models.expense_forecaster import ExpenseForecaster, ForecastOutputContract
from ml.registry.promotion import ModelRegistry

logger = logging.getLogger("sohoj.ml.inference")


@runtime_checkable
class MLModel(Protocol):
    """Common interface required for all production ML models."""

    model_name: str
    model_version: str

    def predict(self, *args: Any, **kwargs: Any) -> Any:
        """Run model inference."""
        ...

    def explain(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Return structured non-judgmental explanations."""
        ...


class BehaviorModelWrapper:
    """Wrapper adapting BehaviorClassifier to the MLModel protocol."""

    model_name = "behavior_classifier"

    def __init__(self, model: BehaviorClassifier) -> None:
        self.model = model
        self.model_version = model.model_version

    def predict(self, *args: Any, **kwargs: Any) -> Any:
        return self.model.predict(*args, **kwargs)

    def explain(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        factors = self.model.explain(*args, **kwargs)
        return {"factors": factors}


class AnomalyModelWrapper:
    """Wrapper adapting UnifiedAnomalyDetector to the MLModel protocol."""

    model_name = "anomaly_detector"

    def __init__(self, detector: UnifiedAnomalyDetector) -> None:
        self.detector = detector
        self.model_version = detector.model_version

    def predict(self, *args: Any, **kwargs: Any) -> Any:
        return self.detector.evaluate_transaction(*args, **kwargs)

    def explain(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        res = self.detector.evaluate_transaction(*args, **kwargs)
        return res.explanation


class FallbackBehaviorModel:
    """Deterministic rule-based fallback when Model A artifact is unavailable."""

    model_name = "behavior_classifier"
    model_version = "v0.0.0_rule_fallback"

    def __init__(self) -> None:
        self.baseline = RuleBasedBehaviorClassifier()

    def predict(self, **kwargs: Any) -> BehaviorPrediction:
        features = kwargs.get("features", kwargs)
        sr = float(features.get("savings_rate", 0.15))
        vol = float(features.get("volatility_cv", 0.1))
        co_r = float(features.get("cashout_ratio", 0.05))
        co_c = float(features.get("cashout_count", 1.0))
        ns = float(features.get("necessity_share", 0.70))
        ds = float(features.get("discretionary_share", 0.15))
        base_pred = self.baseline.predict(
            savings_rate=sr,
            volatility_cv=vol,
            cashout_ratio=co_r,
            cashout_count=co_c,
            necessity_share=ns,
            discretionary_share=ds,
        )
        return BehaviorPrediction(
            profile=base_pred.profile,
            confidence=base_pred.confidence,
            top_factors=base_pred.top_factors,
            is_cold_start=base_pred.is_cold_start,
        )

    def explain(self, **kwargs: Any) -> dict[str, Any]:
        pred = self.predict(**kwargs)
        return {
            "profile": pred.profile,
            "confidence": pred.confidence,
            "top_factors": pred.top_factors,
            "fallback_used": True,
        }


class FallbackAnomalyModel:
    """Deterministic peer-group MAD fallback when Model B artifact is unavailable."""

    model_name = "anomaly_detector"
    model_version = "v0.0.0_peer_fallback"

    def __init__(self) -> None:
        self.detector = UnifiedAnomalyDetector()

    def predict(self, **kwargs: Any) -> AnomalyOutputContract:
        amt = kwargs.get("amount", 0.0)
        cat = kwargs.get("category", "other")
        return self.detector.evaluate_transaction(amount=amt, category=cat)

    def explain(self, **kwargs: Any) -> dict[str, Any]:
        res = self.predict(**kwargs)
        return res.explanation


class FallbackForecasterModel:
    """Deterministic 3-month moving average fallback when Model C artifact is unavailable."""

    model_name = "expense_forecaster"
    model_version = "v0.0.0_ma_fallback"

    def __init__(self) -> None:
        self.forecaster = ExpenseForecaster()

    def predict(self, **kwargs: Any) -> ForecastOutputContract:
        return self.forecaster.predict(**kwargs)

    def explain(self, **kwargs: Any) -> dict[str, Any]:
        res = self.predict(**kwargs)
        return res.explanation


class ModelManager:
    """Production serving manager loading and managing all ML models.

    Features:
    1. Loads versioned models resolved via ModelRegistry 'current.json' pointers.
    2. Hot-reloads on demand without restarting the server.
    3. Graceful baseline fallback upon missing or corrupt artifacts.
    """

    def __init__(
        self,
        registry_root: str | Path = "ml/models_registry",
        fallback_artifacts_root: str | Path = "ml/artifacts",
    ) -> None:
        self.registry = ModelRegistry(registry_root)
        self.fallback_root = Path(fallback_artifacts_root)
        self._models: dict[str, MLModel] = {}
        self._fallbacks_active: dict[str, bool] = {
            "behavior_classifier": False,
            "anomaly_detector": False,
            "expense_forecaster": False,
        }

    def load_all_models(self) -> None:
        """Initialize all three core models at application startup."""
        logger.info("Initializing Sohoj ML serving layer...")
        self.load_behavior_classifier()
        self.load_anomaly_detector()
        self.load_expense_forecaster()
        logger.info("ML serving layer successfully initialized.")

    def load_behavior_classifier(self) -> MLModel:
        """Load Model A (Behavior Classifier) with graceful fallback."""
        try:
            # Check registry first, then fallback to artifacts
            try:
                model_path, ver = self.registry.get_active_model_path("behavior_classifier")
                meta_path = model_path.parent / "metadata.json"
            except FileNotFoundError:
                model_path = self.fallback_root / "behavior_classifier_v1.joblib"
                meta_path = self.fallback_root / "behavior_classifier_v1_metadata.json"

            base_model = BehaviorClassifier.load(model_path, meta_path)
            wrapped_b: MLModel = BehaviorModelWrapper(base_model)
            self._models["behavior_classifier"] = wrapped_b
            self._fallbacks_active["behavior_classifier"] = False
            logger.info(
                "BehaviorClassifier %s loaded cleanly from %s", base_model.model_version, model_path
            )
            return wrapped_b
        except Exception as e:
            logger.warning(
                "Failed to load BehaviorClassifier artifact (%s). Activating FallbackBehaviorModel.",
                e,
            )
            fallback = FallbackBehaviorModel()
            self._models["behavior_classifier"] = fallback
            self._fallbacks_active["behavior_classifier"] = True
            return fallback

    def load_anomaly_detector(self) -> MLModel:
        """Load Model B (Anomaly Detector) with graceful fallback."""
        try:
            try:
                model_path, ver = self.registry.get_active_model_path("anomaly_detector")
            except FileNotFoundError:
                model_path = self.fallback_root / "anomaly_detector_v1.joblib"

            detector = UnifiedAnomalyDetector.load(model_path, verify_checksum=True)
            wrapped_a: MLModel = AnomalyModelWrapper(detector)
            self._models["anomaly_detector"] = wrapped_a
            self._fallbacks_active["anomaly_detector"] = False
            logger.info(
                "UnifiedAnomalyDetector %s loaded cleanly from %s",
                detector.model_version,
                model_path,
            )
            return wrapped_a
        except Exception as e:
            logger.warning(
                "Failed to load UnifiedAnomalyDetector artifact (%s). Activating FallbackAnomalyModel.",
                e,
            )
            fallback = FallbackAnomalyModel()
            self._models["anomaly_detector"] = fallback
            self._fallbacks_active["anomaly_detector"] = True
            return fallback

    def load_expense_forecaster(self) -> MLModel:
        """Load Model C (Expense Forecaster) with graceful fallback."""
        try:
            try:
                model_path, ver = self.registry.get_active_model_path("expense_forecaster")
            except FileNotFoundError:
                model_path = self.fallback_root / "expense_forecaster_v1.joblib"

            forecaster = ExpenseForecaster.load(model_path, verify_checksum=True)
            self._models["expense_forecaster"] = forecaster
            self._fallbacks_active["expense_forecaster"] = False
            logger.info(
                "ExpenseForecaster %s loaded cleanly from %s", forecaster.model_version, model_path
            )
            return forecaster
        except Exception as e:
            logger.warning(
                "Failed to load ExpenseForecaster artifact (%s). Activating FallbackForecasterModel.",
                e,
            )
            fallback = FallbackForecasterModel()
            self._models["expense_forecaster"] = fallback
            self._fallbacks_active["expense_forecaster"] = True
            return fallback

    def get_model(self, model_name: str) -> MLModel:
        """Retrieve model instance, lazily loading if required."""
        if model_name not in self._models:
            if model_name == "behavior_classifier":
                return self.load_behavior_classifier()
            elif model_name == "anomaly_detector":
                return self.load_anomaly_detector()
            elif model_name == "expense_forecaster":
                return self.load_expense_forecaster()
            else:
                raise ValueError(f"Unknown model name '{model_name}'.")
        return self._models[model_name]

    def reload_model(self, model_name: str) -> MLModel:
        """Hot-reload specified model pointer without process restart."""
        logger.info("Hot-reloading model '%s'...", model_name)
        if model_name == "behavior_classifier":
            return self.load_behavior_classifier()
        elif model_name == "anomaly_detector":
            return self.load_anomaly_detector()
        elif model_name == "expense_forecaster":
            return self.load_expense_forecaster()
        else:
            raise ValueError(f"Unknown model name '{model_name}'.")

    def is_fallback_active(self, model_name: str) -> bool:
        """Check whether fallback baseline is currently serving for model_name."""
        return self._fallbacks_active.get(model_name, False)


_MANAGER_INSTANCE: ModelManager | None = None


def get_model_manager() -> ModelManager:
    """Retrieve global ModelManager singleton."""
    global _MANAGER_INSTANCE
    if _MANAGER_INSTANCE is None:
        _MANAGER_INSTANCE = ModelManager()
    return _MANAGER_INSTANCE
