"""Unit tests for Model A: Behavior Classification.

Covers:
1. Checksum-verified artifact loading.
2. Cryptographic tamper detection (SecurityError on mismatch).
3. Cold-start policy (< 2 months active returns 'insufficient_data').
4. Scale invariance property (2x scaling preserves exact prediction).
5. Explainability factors & non-judgmental language requirements.
6. Calibrated probability distributions.
7. Benchmark comparison (beats rule baseline on held-out data, macro-F1 < 0.99).
8. Backend adapter singleton interface.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from backend.app.ml.behavior import get_behavior_classifier
from ml.models.behavior_classifier import (
    BehaviorClassifier,
    SecurityError,
)


@pytest.fixture(scope="module")
def behavior_model() -> BehaviorClassifier:
    """Fixture providing loaded, verified BehaviorClassifier."""
    return get_behavior_classifier()


def test_model_artifact_loading_and_metadata(behavior_model: BehaviorClassifier):
    """Asserts that model loads with correct versioning and classes."""
    assert behavior_model.model_version == "v1.0.0"
    assert behavior_model.feature_schema_version == "v1.0.0"
    assert len(behavior_model.classes) == 6
    assert "consistent_saver" in behavior_model.classes
    assert "tight_budgeter" in behavior_model.classes
    assert len(behavior_model.sha256_checksum) == 64


def test_tamper_detection_triggers_security_error(tmp_path: Path):
    """Asserts that altering artifact content or metadata checksum raises SecurityError."""
    model_file = Path("ml/artifacts/behavior_classifier_v1.joblib")
    meta_file = Path("ml/artifacts/behavior_classifier_v1_metadata.json")

    with open(meta_file, encoding="utf-8") as f:
        meta_data = json.load(f)

    # Corrupt expected checksum in temporary metadata
    tampered_meta = dict(meta_data)
    tampered_meta["sha256_checksum"] = "0" * 64
    temp_meta_path = tmp_path / "tampered_metadata.json"
    with open(temp_meta_path, "w", encoding="utf-8") as f:
        json.dump(tampered_meta, f)

    with pytest.raises(SecurityError, match="integrity check failed"):
        BehaviorClassifier.load(model_file, temp_meta_path)


def test_cold_start_policy(behavior_model: BehaviorClassifier):
    """Confirms that < 2 months of history strictly returns 'insufficient_data'."""
    features = {
        "savings_rate": 0.30,
        "necessity_rate": 0.50,
        "discretionary_rate": 0.20,
        "txn_count": 15,
        "cashout_count": 2,
    }

    pred_0 = behavior_model.predict(features, months_active=0)
    assert pred_0.profile == "insufficient_data"
    assert pred_0.is_cold_start is True
    assert pred_0.confidence == 0.0

    pred_1 = behavior_model.predict(features, months_active=1)
    assert pred_1.profile == "insufficient_data"
    assert pred_1.is_cold_start is True
    assert pred_1.confidence == 0.0

    pred_2 = behavior_model.predict(features, months_active=2)
    assert pred_2.profile != "insufficient_data"
    assert pred_2.is_cold_start is False
    assert pred_2.confidence > 0.0


def test_scale_invariance_property(behavior_model: BehaviorClassifier):
    """Property test: Multiplying all absolute monetary figures by 2.0x yields identical label and confidence."""
    base_record = {
        "income": 35000.0,
        "expense": 22000.0,
        "savings": 8000.0,
        "savings_rate": 0.2285,
        "necessity_expense": 18000.0,
        "discretionary_expense": 4000.0,
        "necessity_rate": 0.8181,
        "discretionary_rate": 0.1818,
        "income_expense_ratio": 1.5909,
        "txn_count": 18,
        "cashout_count": 3,
        "avg_txn": 1944.44,
        "expense_variance": 450000.0,
        "rolling_expense_3m_mean": 21000.0,
        "spending_trend_3m": 500.0,
        "rolling_savings_rate_3m_mean": 0.22,
        "rolling_savings_rate_3m_std": 0.02,
        "savings_consistency": 0.98,
        "category_entropy_3m": 1.85,
        "discretionary_volatility_3m": 0.04,
        "deficit_months_3m": 0,
        "spending_growth": 0.05,
    }

    # Scaled by 2x
    scaled_record = dict(base_record)
    scaled_record["income"] = base_record["income"] * 2.0
    scaled_record["expense"] = base_record["expense"] * 2.0
    scaled_record["savings"] = base_record["savings"] * 2.0
    scaled_record["necessity_expense"] = base_record["necessity_expense"] * 2.0
    scaled_record["discretionary_expense"] = base_record["discretionary_expense"] * 2.0
    scaled_record["avg_txn"] = base_record["avg_txn"] * 2.0
    scaled_record["expense_variance"] = base_record["expense_variance"] * 4.0
    scaled_record["rolling_expense_3m_mean"] = base_record["rolling_expense_3m_mean"] * 2.0
    scaled_record["spending_trend_3m"] = base_record["spending_trend_3m"] * 2.0

    p_base = behavior_model.predict(base_record, months_active=12)
    p_scaled = behavior_model.predict(scaled_record, months_active=12)

    assert p_base.profile == p_scaled.profile
    assert abs(p_base.confidence - p_scaled.confidence) < 1e-4


def test_explainability_non_judgmental_factors(behavior_model: BehaviorClassifier):
    """Confirms explainability factors use non-judgmental, purely descriptive wording."""
    features = {
        "savings_rate": 0.02,
        "necessity_rate": 0.90,
        "discretionary_rate": 0.08,
        "income_expense_ratio": 0.98,
        "txn_count": 20,
        "cashout_count": 8,
    }

    pred = behavior_model.predict(features, months_active=12)
    assert len(pred.top_factors) >= 1

    moralizing_words = ["good", "bad", "poor", "lazy", "foolish", "ideal", "virtuous", "sinful"]
    for factor in pred.top_factors:
        label = factor.get("label", "").lower()
        for word in moralizing_words:
            assert word not in label, f"Moralizing term '{word}' found in explanation: {label}"


def test_calibrated_probabilities_sum_to_one(behavior_model: BehaviorClassifier):
    """Validates that calibrated probabilities form a valid probability distribution."""
    features = {
        "savings_rate": 0.15,
        "necessity_rate": 0.65,
        "discretionary_rate": 0.20,
        "income_expense_ratio": 1.10,
        "txn_count": 12,
        "cashout_count": 3,
    }

    pred = behavior_model.predict(features, months_active=12)
    probs = pred.class_probabilities
    assert len(probs) == 6

    prob_sum = sum(probs.values())
    assert abs(prob_sum - 1.0) < 1e-3
    assert all(0.0 <= p <= 1.0 for p in probs.values())


def test_beats_rule_baseline_on_heldout():
    """Asserts that Model A beats the rule-based baseline on held-out seed data.

    Acceptance criteria:
    - Beats rule baseline on Macro-F1 on held-out cohort.
    - Strong performance but not suspiciously perfect (< 0.99 to verify no target leakage).
    """
    meta_path = Path("ml/artifacts/behavior_classifier_v1_metadata.json")
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    rule_f1 = meta["cv_benchmarks"]["rule_baseline"]["macro_f1_mean"]
    heldout_f1 = meta["heldout_metrics"]["macro_f1"]
    heldout_acc = meta["heldout_metrics"]["accuracy"]
    heldout_auc = meta["heldout_metrics"]["roc_auc_ovr"]
    heldout_ece = meta["heldout_metrics"]["ece"]

    assert heldout_f1 > rule_f1, (
        f"Model A ({heldout_f1:.4f}) did not beat rule baseline ({rule_f1:.4f})"
    )
    assert heldout_f1 < 0.99, (
        f"Suspiciously perfect Macro-F1 ({heldout_f1:.4f}) indicates potential data leakage"
    )
    assert heldout_acc > 0.70
    assert heldout_auc > 0.90
    assert heldout_ece < 0.10, f"Expected Calibration Error {heldout_ece} is above threshold 0.10"
