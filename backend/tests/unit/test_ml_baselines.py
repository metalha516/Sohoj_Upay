"""Unit tests for ML rule-based baselines and baseline evaluation functions."""

from decimal import Decimal

import numpy as np
import pytest
from ml.evaluation.evaluate_baselines import compute_smape
from ml.models.baselines import (
    ExpenseForecasterBaseline,
    RobustZScoreAnomalyDetector,
    RuleBasedBehaviorClassifier,
)


def test_rule_based_behavior_classifier_cold_start() -> None:
    """Verify that users with less than 2 months of history receive insufficient_data."""
    clf = RuleBasedBehaviorClassifier()
    res = clf.predict(
        savings_rate=0.25,
        cashout_ratio=0.10,
        cashout_count=1.0,
        necessity_share=0.70,
        discretionary_share=0.20,
        months_active=1,
    )
    assert res.profile == "insufficient_data"
    assert res.is_cold_start is True
    assert res.confidence == 0.0


def test_rule_based_behavior_classifier_personas() -> None:
    """Verify rule thresholds identify key behavioral archetypes."""
    clf = RuleBasedBehaviorClassifier()

    # Cash-dominant transactor
    res_cash = clf.predict(
        savings_rate=0.05,
        cashout_ratio=0.60,
        cashout_count=4.0,
        necessity_share=0.75,
        discretionary_share=0.10,
        months_active=6,
    )
    assert res_cash.profile == "cash_dominant_transactor"
    assert res_cash.confidence > 0.70

    # Consistent saver
    res_saver = clf.predict(
        savings_rate=0.25,
        cashout_ratio=0.10,
        cashout_count=1.0,
        necessity_share=0.65,
        discretionary_share=0.20,
        months_active=6,
    )
    assert res_saver.profile == "consistent_saver"

    # Tight budgeter
    res_budget = clf.predict(
        savings_rate=0.02,
        cashout_ratio=0.20,
        cashout_count=2.0,
        necessity_share=0.88,
        discretionary_share=0.05,
        months_active=6,
    )
    assert res_budget.profile == "tight_budgeter"

    # Discretionary spender
    res_disc = clf.predict(
        savings_rate=0.03,
        cashout_ratio=0.15,
        cashout_count=1.5,
        necessity_share=0.55,
        discretionary_share=0.35,
        months_active=6,
    )
    assert res_disc.profile == "discretionary_spender"

    # Volatile earner
    res_vol = clf.predict(
        savings_rate=0.10,
        cashout_ratio=0.20,
        cashout_count=2.0,
        necessity_share=0.70,
        discretionary_share=0.15,
        volatility_cv=0.45,
        months_active=6,
    )
    assert res_vol.profile == "volatile_earner"

    # Balanced spender (fallback)
    res_bal = clf.predict(
        savings_rate=0.10,
        cashout_ratio=0.25,
        cashout_count=2.0,
        necessity_share=0.70,
        discretionary_share=0.15,
        volatility_cv=0.15,
        months_active=6,
    )
    assert res_bal.profile == "balanced_spender"


def test_robust_z_score_anomaly_detector() -> None:
    """Verify MAD anomaly detector identifies extreme spikes and uses peer fallback."""
    detector = RobustZScoreAnomalyDetector(z_threshold=3.5, min_history_samples=10)

    # Established history (15 samples)
    normal_history = [
        500.0,
        520.0,
        480.0,
        510.0,
        490.0,
        530.0,
        470.0,
        500.0,
        515.0,
        485.0,
        505.0,
        495.0,
    ]

    # Normal amount (550 BDT)
    res_normal = detector.detect(amount=550.0, user_history=normal_history)
    assert res_normal.is_anomaly is False
    assert res_normal.fallback_used is False
    assert abs(res_normal.score) < 3.5

    # Extreme spike amount (15,000 BDT)
    res_spike = detector.detect(amount=Decimal("15000.00"), user_history=normal_history)
    assert res_spike.is_anomaly is True
    assert res_spike.score > 3.5
    assert res_spike.observed == 15000.0
    assert res_spike.baseline_median == pytest.approx(500.0, abs=10.0)

    # Cold start (< 10 samples) triggers fallback to peer stats
    short_history = [300.0, 400.0]
    res_fallback = detector.detect(
        amount=450.0, user_history=short_history, peer_median=500.0, peer_mad=150.0
    )
    assert res_fallback.fallback_used is True
    assert res_fallback.baseline_median == 500.0
    assert res_fallback.is_anomaly is False


def test_robust_z_score_zero_mad_protection() -> None:
    """Verify detector handles zero variance/constant values gracefully."""
    detector = RobustZScoreAnomalyDetector(z_threshold=3.5, min_history_samples=5)
    identical_history = [500.0] * 12
    res = detector.detect(amount=500.0, user_history=identical_history)
    assert res.is_anomaly is False
    assert res.score == 0.0


def test_expense_forecaster_baselines() -> None:
    """Verify naive and moving average expense forecasters."""
    forecaster = ExpenseForecasterBaseline()

    # Empty history
    res_empty_naive = forecaster.predict_naive([])
    assert res_empty_naive.forecast == 0.0

    res_empty_sma = forecaster.predict_moving_average([], window=3)
    assert res_empty_sma.forecast == 0.0

    # 5 months of expense history
    history = [12000.0, 14000.0, 13000.0, 15000.0, 16000.0]

    # Naive: equals last month (16,000)
    res_naive = forecaster.predict_naive(history)
    assert res_naive.forecast == 16000.0
    assert res_naive.method == "naive"
    assert res_naive.lower_bound < res_naive.forecast < res_naive.upper_bound

    # 3-Month Moving Average: mean of last 3 (13000, 15000, 16000) = 14666.67
    res_sma = forecaster.predict_moving_average(history, window=3)
    assert res_sma.forecast == pytest.approx(14666.67, abs=0.1)
    assert res_sma.historical_points_used == 3
    assert res_sma.lower_bound < res_sma.forecast < res_sma.upper_bound


def test_compute_smape() -> None:
    """Verify symmetric MAPE calculation."""
    actual = np.array([100.0, 200.0, 300.0])
    pred_exact = np.array([100.0, 200.0, 300.0])
    assert compute_smape(actual, pred_exact) == 0.0

    pred_off = np.array([110.0, 190.0, 330.0])
    smape_val = compute_smape(actual, pred_off)
    assert 0.0 < smape_val < 15.0
