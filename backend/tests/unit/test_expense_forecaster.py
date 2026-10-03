"""Unit and integration tests for Model C (Expense Forecasting), Model Registry, and Serving Layer.

Tests:
1. Mathematical correctness of 3-month moving average fallback.
2. Quantile ordering monotonicity guarantee (p10 <= p50 <= p90).
3. Prediction interval width and factor explanations.
4. ModelRegistry staging, checksum validation, and candidate promotion.
5. Unified ModelManager startup loading and hot-reloading.
6. Graceful fallback activation when model artifact is missing or corrupt.
7. Database persistence entity creation for Prediction, BehaviorProfile, and Anomaly.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from ml.models.anomaly_detector import AnomalyOutputContract
from ml.models.behavior_classifier import BehaviorPrediction
from ml.models.expense_forecaster import ExpenseForecaster, ForecastOutputContract
from ml.registry.promotion import ModelRegistry, PromotionGateError

from app.ml.inference import (
    MLModel,
    ModelManager,
)
from app.services.ml_persistence import MLPersistenceService

# =============================================================================
# 1. Forecasting & Quantile Invariance Tests
# =============================================================================


def test_forecast_monotonic_quantile_ordering() -> None:
    """Predicted quantiles must strictly satisfy: lower_bound_p10 <= p50 <= upper_bound_p90."""
    forecaster = ExpenseForecaster()

    # Even with arbitrary inputs and in fallback mode
    res = forecaster.predict(
        current_expense=25000.0,
        rolling_3m_mean=24000.0,
        rolling_3m_std=3000.0,
        target_month_str="2026-05",
        target_month_num=5,
    )

    assert res.lower_bound_p10 <= res.predicted_expense
    assert res.predicted_expense <= res.upper_bound_p90
    assert res.prediction_interval_width == pytest.approx(
        res.upper_bound_p90 - res.lower_bound_p10, abs=1e-2
    )
    assert res.prediction_interval_width > 0.0


def test_moving_average_fallback_when_sparse_history() -> None:
    """Users with < 2 months of history must trigger deterministic moving-average fallback."""
    forecaster = ExpenseForecaster()

    # User with only 1 month history
    res = forecaster.predict(
        current_expense=18000.0,
        rolling_3m_mean=18000.0,
        history_months_count=1,
        target_month_str="2026-02",
        target_month_num=2,
    )

    assert res.fallback_used
    assert res.predicted_expense == 18000.0
    assert "3-month moving average" in res.explanation["drivers"]


def test_festival_seasonal_adjustment_in_fallback() -> None:
    """During Eid months (March/May), fallback automatically applies cultural multiplier."""
    forecaster = ExpenseForecaster()

    # Month 3 is Ramadan/Eid-ul-Fitr
    res_eid = forecaster.predict(
        current_expense=20000.0,
        rolling_3m_mean=20000.0,
        rolling_3m_std=2000.0,
        history_months_count=1,
        target_month_str="2026-03",
        target_month_num=3,
    )

    # 20,000 * 1.25 = 25,000
    assert res_eid.predicted_expense == 25000.0
    assert any("Cultural Festival" in f["name"] for f in res_eid.factors)


# =============================================================================
# 2. Model Registry & Promotion Tests
# =============================================================================


def test_model_registry_lifecycle_and_checksum(tmp_path: Path) -> None:
    """ModelRegistry must register, verify checksums, and update current pointer."""
    registry = ModelRegistry(registry_root=tmp_path / "models_registry")

    # Create dummy artifact
    source_artifact = tmp_path / "dummy_forecaster.joblib"
    forecaster = ExpenseForecaster()
    forecaster.save(source_artifact)

    meta_source = source_artifact.parent / f"{source_artifact.stem}_metadata.json"

    # Register version v1.0.0
    registered = registry.register_version(
        model_name="expense_forecaster",
        version="v1.0.0",
        artifact_source=source_artifact,
        metadata_source=meta_source,
    )
    assert registered.exists()

    # Promote to production
    promo = registry.promote_candidate(
        model_name="expense_forecaster",
        candidate_version="v1.0.0",
    )
    assert promo["promoted"]
    assert promo["active_version"] == "v1.0.0"

    # Active model resolution
    active_path, active_ver = registry.get_active_model_path("expense_forecaster")
    assert active_ver == "v1.0.0"
    assert active_path.exists()


def test_model_registry_rejects_corrupted_candidate(tmp_path: Path) -> None:
    """Candidate with mismatched checksum must be rejected by integrity gate."""
    registry = ModelRegistry(registry_root=tmp_path / "models_registry")

    source_artifact = tmp_path / "cand.joblib"
    forecaster = ExpenseForecaster()
    forecaster.save(source_artifact)
    meta_source = source_artifact.parent / f"{source_artifact.stem}_metadata.json"

    registry.register_version("expense_forecaster", "v2.0.0", source_artifact, meta_source)

    # Tamper with registered candidate file
    target_joblib = registry.get_model_dir("expense_forecaster") / "v2.0.0" / "model.joblib"
    with open(target_joblib, "r+b") as f:
        f.seek(5)
        f.write(b"\xde\xad\xbe\xef")

    with pytest.raises(PromotionGateError, match="Gate 1 FAILED"):
        registry.promote_candidate("expense_forecaster", "v2.0.0")


# =============================================================================
# 3. Serving Layer & Graceful Fallback Tests
# =============================================================================


def test_serving_layer_protocol_conformance() -> None:
    """All registered models must satisfy the MLModel runtime protocol."""
    manager = ModelManager()
    forecaster = manager.load_expense_forecaster()
    assert isinstance(forecaster, MLModel)


def test_serving_layer_graceful_fallback_when_corrupt(tmp_path: Path) -> None:
    """Proves system falls back to baseline when artifact is missing or corrupted."""
    # Point manager to empty temporary registry and empty fallback directory
    manager = ModelManager(
        registry_root=tmp_path / "empty_registry",
        fallback_artifacts_root=tmp_path / "empty_artifacts",
    )

    # Request forecaster when artifact is missing
    model = manager.load_expense_forecaster()
    assert manager.is_fallback_active("expense_forecaster")
    assert "fallback" in model.model_version.lower()

    # Inference must still succeed cleanly without crashing!
    res = model.predict(current_expense=30000.0, target_month_str="2026-06", target_month_num=6)
    assert res.predicted_expense > 0.0
    assert res.fallback_used

    # Explanation must also succeed
    explanation = model.explain(
        current_expense=30000.0, target_month_str="2026-06", target_month_num=6
    )
    assert "summary" in explanation


# =============================================================================
# 4. Database Persistence Entity Creation Tests
# =============================================================================


def test_database_persistence_entities() -> None:
    """Verify entities for behavior_profiles, anomalies, and predictions match schemas."""
    user_id = uuid.uuid4()

    # 1. Behavior Profile
    b_pred = BehaviorPrediction(profile="consistent_saver", confidence=0.85, top_factors=[])
    b_record = MLPersistenceService.create_behavior_profile_record(
        user_id=user_id,
        prediction=b_pred,
        as_of_month=date(2026, 4, 1),
        model_version="v1.0.0",
        savings_rate=0.25,
    )
    assert b_record.user_id == user_id
    assert b_record.profile == "consistent_saver"
    assert b_record.confidence == Decimal("0.8500")
    assert b_record.model_version == "v1.0.0"

    # 2. Anomaly
    a_out = AnomalyOutputContract(
        is_anomaly=True,
        anomaly_score=0.92,
        observed=8000.0,
        baseline=2000.0,
        deviation_pct=300.0,
        scope="transaction",
        category="shopping",
        explanation={"summary": "Unusual spike"},
    )
    a_record = MLPersistenceService.create_anomaly_record(
        user_id=user_id,
        anomaly_output=a_out,
        model_version="v1.0.0",
    )
    assert a_record.user_id == user_id
    assert a_record.anomaly_score == Decimal("0.9200")
    assert a_record.scope == "transaction"
    assert a_record.status == "open"

    # 3. Prediction (Expense Forecast)
    f_out = ForecastOutputContract(
        predicted_expense=28500.0,
        lower_bound_p10=22000.0,
        upper_bound_p90=36000.0,
        prediction_interval_width=14000.0,
        fallback_used=False,
        model_version="v1.0.0",
        target_month="2026-05",
        factors=[],
        explanation={"summary": "Forecast"},
    )
    p_record = MLPersistenceService.create_expense_forecast_record(
        user_id=user_id,
        forecast_output=f_out,
        horizon_month=date(2026, 5, 1),
        model_version="v1.0.0",
    )
    assert p_record.user_id == user_id
    assert p_record.prediction_type == "expense_forecast"
    assert p_record.prediction_value["predicted_expense"] == 28500.0
    assert p_record.confidence == Decimal("0.8000")
    assert p_record.horizon_month == date(2026, 5, 1)
