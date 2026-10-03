"""Unit tests for ML drift and stability metrics (PSI, KS, MAPE)."""

import numpy as np
import pytest
from app.worker.drift_job import calculate_ks, calculate_mape, calculate_psi


def test_psi_identical_distributions():
    # If reference and current are identical samples, PSI should be very close to 0.0
    ref = np.random.normal(loc=100.0, scale=15.0, size=500)
    cur = ref.copy()
    psi = calculate_psi(ref, cur)
    assert psi < 0.05, f"PSI should be near zero for identical data, got {psi}"


def test_psi_shifted_distribution():
    # When distribution shifts significantly, PSI should exceed 0.25
    ref = np.random.normal(loc=50.0, scale=10.0, size=500)
    cur = np.random.normal(loc=150.0, scale=10.0, size=500)
    psi = calculate_psi(ref, cur)
    assert psi >= 0.25, f"PSI should detect heavy shift, got {psi}"


def test_ks_statistic_identical_and_different():
    ref = np.linspace(0, 100, 100)
    cur = np.linspace(0, 100, 100)
    d_same = calculate_ks(ref, cur)
    assert d_same == 0.0

    cur_shifted = np.linspace(50, 150, 100)
    d_diff = calculate_ks(ref, cur_shifted)
    assert d_diff > 0.4


def test_mape_calculation():
    actuals = [100.0, 200.0, 300.0]
    preds = [110.0, 190.0, 315.0]
    # Errors: 10/100 = 0.1, 10/200 = 0.05, 15/300 = 0.05. Mean = 0.2 / 3 = 0.0667
    mape = calculate_mape(actuals, preds)
    assert pytest.approx(mape, rel=1e-2) == 0.0667


def test_empty_or_small_data_resilience():
    assert calculate_psi([], []) == 0.0
    assert calculate_ks([], []) == 0.0
    assert calculate_mape([], []) == 0.0
