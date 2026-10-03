"""Unit tests for Model B (Anomaly Detection).

Tests:
1. Robust Z-score and MAD calculation correctness.
2. Peer-group fallback on sparse history (< 20 txns) with minimum group size >= 20.
3. Edge cases: new category, first transaction of user, zero baseline, zero MAD.
4. Seasonality / festival calibration impact on festive transactions.
5. Alert budget ceiling enforcement (<= 3 alerts/user/month).
6. Analyst feedback recording, metrics tracking, and adaptive threshold tuning.
7. Cryptographic tamper detection rejecting altered artifacts.
8. Non-judgmental language contract verification.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import numpy as np
import pytest
from ml.models.anomaly_detector import AnomalyOutputContract, UnifiedAnomalyDetector
from ml.models.transaction_anomaly import TransactionAnomalyDetector

from app.services.anomaly_feedback import AnomalyFeedbackService

# =============================================================================
# 1. Deviation Math & Robust Z-Score Tests
# =============================================================================


def test_robust_z_score_mad_calculation() -> None:
    """Verify MAD and modified Z-Score match Boris Iglewicz & David Hoaglin standard."""
    detector = TransactionAnomalyDetector(z_threshold=3.5, min_history_samples=20)

    # Synthetic baseline: 25 observations with median 500, MAD ~ 100
    user_id = "user_test_1"
    category = "groceries"

    # Set explicit baseline
    detector.user_baselines[(user_id, category)] = (500.0, 100.0, 25)

    # 1. Normal amount (550.0): dev = 50, modified_z = 0.6745 * 50 / 100 = 0.337 < 3.5
    res_normal = detector.detect(amount=550.0, category=category, user_id=user_id)
    assert not res_normal.is_anomaly
    assert res_normal.observed == 550.0
    assert res_normal.baseline == 500.0
    assert res_normal.deviation_pct == 10.0
    assert not res_normal.fallback_used
    assert res_normal.peer_group_size == 25

    # 2. Spiked amount (2500.0): dev = 2000, modified_z = 0.6745 * 2000 / 100 = 13.49 >= 3.5
    res_spike = detector.detect(amount=2500.0, category=category, user_id=user_id)
    assert res_spike.is_anomaly
    assert res_spike.observed == 2500.0
    assert res_spike.deviation_pct == 400.0
    assert res_spike.anomaly_score >= 0.80
    assert "higher than baseline" in res_spike.anomaly_reasons[0]


# =============================================================================
# 2. Peer-Group Fallback & Sparse History Tests
# =============================================================================


def test_peer_group_fallback_on_sparse_history() -> None:
    """When a user has < 20 transactions, detector must fall back to peer-group stats."""
    detector = TransactionAnomalyDetector(z_threshold=3.5, min_history_samples=20)

    user_id = "user_sparse"
    category = "dining"

    # User only has 5 transactions -> sparse!
    detector.user_baselines[(user_id, category)] = (800.0, 200.0, 5)
    # Global category baseline has 1500 samples
    detector.global_baselines[category] = (450.0, 150.0, 1500)

    res = detector.detect(amount=500.0, category=category, user_id=user_id)
    # Fallback should be triggered
    assert res.fallback_used
    # Baseline used should be global (450.0), NOT user's sparse (800.0)
    assert res.baseline == 450.0
    assert res.peer_group_size == 1500
    assert res.peer_group_size >= 20


# =============================================================================
# 3. Edge Cases: New Category, First Txn, Zero Baseline
# =============================================================================


def test_edge_case_brand_new_category() -> None:
    """A completely novel category unknown to both user and global baselines."""
    detector = TransactionAnomalyDetector()
    res = detector.detect(amount=350.0, category="completely_unknown_category", user_id="u_new")

    assert res.fallback_used
    assert res.baseline > 0.0
    assert res.peer_group_size >= 20
    assert not res.is_anomaly  # Reasonable amount under default baseline


def test_edge_case_first_transaction_of_user() -> None:
    """User with zero previous transaction history."""
    detector = TransactionAnomalyDetector()
    detector.global_baselines["utilities"] = (1200.0, 300.0, 500)

    res = detector.detect(amount=1300.0, category="utilities", user_id="user_first_ever")
    assert res.fallback_used
    assert res.baseline == 1200.0
    assert not res.is_anomaly


def test_edge_case_zero_baseline_and_zero_mad() -> None:
    """Zero baseline and zero MAD must not trigger ZeroDivisionError or negative math errors."""
    detector = TransactionAnomalyDetector()
    detector.user_baselines[("u_zero", "bazaar")] = (0.0, 0.0, 25)

    # Safe MAD should floor to at least 1.0
    res = detector.detect(amount=0.0, category="bazaar", user_id="u_zero")
    assert not res.is_anomaly
    assert res.observed == 0.0

    # Non-zero transaction with 0.0 baseline
    res_pos = detector.detect(amount=100.0, category="bazaar", user_id="u_zero")
    assert res_pos.observed == 100.0
    assert not np.isnan(res_pos.anomaly_score)


# =============================================================================
# 4. Seasonality / Festival Awareness Tests
# =============================================================================


def test_festival_awareness_prevents_false_positives() -> None:
    """During Eid, shopping baseline is elevated (3.2x), preventing false alerts."""
    detector = TransactionAnomalyDetector(z_threshold=3.5)
    detector.user_baselines[("u_eid", "shopping")] = (2000.0, 500.0, 30)

    normal_eid_shopping = 6000.0  # 3x regular baseline, completely normal for Eid

    # 1. Naive detection (multiplier = 1.0): 6000 vs 2000 => dev=4000, mod_z=5.4 => FALSE POSITIVE!
    naive_res = detector.detect(
        amount=normal_eid_shopping,
        category="shopping",
        user_id="u_eid",
        festival_multiplier=1.0,
    )
    assert naive_res.is_anomaly
    assert not naive_res.festival_adjusted

    # 2. Festival-aware detection (multiplier = 3.2): baseline=6400 => dev=-400 => LEGITIMATE FESTIVAL SPEND!
    aware_res = detector.detect(
        amount=normal_eid_shopping,
        category="shopping",
        user_id="u_eid",
        festival_multiplier=3.2,
    )
    assert not aware_res.is_anomaly
    assert aware_res.festival_adjusted
    assert aware_res.festival_multiplier == 3.2
    assert aware_res.baseline == 6400.0

    # 3. Extreme fraud spike (30,000 Tk): still caught even during Eid!
    fraud_res = detector.detect(
        amount=30000.0,
        category="shopping",
        user_id="u_eid",
        festival_multiplier=3.2,
    )
    assert fraud_res.is_anomaly
    assert fraud_res.observed == 30000.0


# =============================================================================
# 5. Alert Budget Enforcement (<= 3 Alerts / User / Month)
# =============================================================================


def test_alert_budget_enforcement() -> None:
    """Alert budget policy must cap active alerts to <= 3 per user per month."""
    unified = UnifiedAnomalyDetector()

    # Create 6 candidate anomalies with descending scores
    candidates = [
        AnomalyOutputContract(
            is_anomaly=True,
            anomaly_score=0.95 - (i * 0.05),
            observed=5000.0 + i * 1000,
            baseline=1000.0,
            deviation_pct=400.0 + i * 100,
            scope="transaction",
            category="dining",
            explanation={"summary": f"Alert {i + 1}"},
        )
        for i in range(6)
    ]

    budgeted = unified.apply_alert_budget(candidates, max_alerts=3)
    assert len(budgeted) == 6

    # Top 3 must remain active anomalies
    active_alerts = [b for b in budgeted if b.is_anomaly]
    assert len(active_alerts) == 3
    assert [round(a.anomaly_score, 2) for a in active_alerts] == [0.95, 0.90, 0.85]

    # Remaining 3 must be budget_suppressed=True and is_anomaly=False
    suppressed = [b for b in budgeted if b.budget_suppressed]
    assert len(suppressed) == 3
    for s in suppressed:
        assert not s.is_anomaly
        assert s.budget_suppressed


# =============================================================================
# 6. Analyst Feedback & Adaptive Threshold Tuning
# =============================================================================


def test_analyst_feedback_and_adaptive_tuning() -> None:
    """Analyst feedback must track confirmations/dismissals and adjust thresholds."""
    feedback_service = AnomalyFeedbackService()
    user_id = uuid.uuid4()
    anomaly_id_1 = uuid.uuid4()
    anomaly_id_2 = uuid.uuid4()
    anomaly_id_3 = uuid.uuid4()

    # Record 1 confirmed and 2 dismissed anomalies
    feedback_service.record_feedback(
        anomaly_id=anomaly_id_1,
        user_id=user_id,
        category="dining",
        status="dismissed",
        notes="Legitimate dinner with visiting relatives",
    )
    feedback_service.record_feedback(
        anomaly_id=anomaly_id_2,
        user_id=user_id,
        category="dining",
        status="dismissed",
        notes="Weekend family dinner",
    )
    feedback_service.record_feedback(
        anomaly_id=anomaly_id_3,
        user_id=user_id,
        category="dining",
        status="confirmed",
        notes="Unauthorized duplicate charge",
    )

    metrics = feedback_service.get_feedback_metrics(user_id)
    assert metrics.total_reviewed == 3
    assert metrics.confirmed_count == 1
    assert metrics.dismissed_count == 2
    assert metrics.dismissal_rate == pytest.approx(0.6667, abs=1e-3)

    # Adaptive threshold should relax for dining due to high dismissal rate
    adjusted_th = feedback_service.compute_adaptive_threshold_offset(
        user_id=user_id, category="dining", base_z_threshold=3.5
    )
    assert adjusted_th > 3.5


# =============================================================================
# 7. Non-Judgmental Language Policy
# =============================================================================


def test_non_judgmental_language_contract() -> None:
    """Detector must reject judgmental words in explanations."""
    unified = UnifiedAnomalyDetector()

    # Valid non-judgmental explanation passes
    valid_explanation = {
        "summary": "Unusual activity: Transaction amount ৳5,000 is 3.5x higher than baseline.",
        "tone": "descriptive",
    }
    unified._validate_non_judgmental(valid_explanation)

    # Moralizing explanation raises ValueError
    judgmental_explanation = {
        "summary": "You made a bad and wasteful purchase that is irresponsible.",
        "tone": "judgmental",
    }
    with pytest.raises(ValueError, match="Violation of non-judgmental language contract"):
        unified._validate_non_judgmental(judgmental_explanation)


# =============================================================================
# 8. Cryptographic Tamper Detection
# =============================================================================


def test_cryptographic_tamper_detection(tmp_path: Path) -> None:
    """Tampered artifact must fail checksum verification."""
    detector = UnifiedAnomalyDetector()
    model_file = tmp_path / "anomaly_test.joblib"
    detector.save(model_file)

    # Clean load should succeed
    loaded = UnifiedAnomalyDetector.load(model_file, verify_checksum=True)
    assert loaded.model_version == "v1.0.0"

    # Tamper with file
    with open(model_file, "r+b") as f:
        f.seek(10)
        f.write(b"\xff\xfe\xfd")

    with pytest.raises(PermissionError, match="Cryptographic tamper check FAILED"):
        UnifiedAnomalyDetector.load(model_file, verify_checksum=True)
