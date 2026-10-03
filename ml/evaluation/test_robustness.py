"""Robustness and Invariance Validation Suite for Model A (Behavior Classification).

Tests:
1. Scale Invariance (2x scaling of currency amounts preserves identical label & confidence).
2. Noise Perturbation Tolerance (+/- 5% Gaussian noise achieves >= 90% label agreement).
3. Cold-Start Handling (< 2 months active returns 'insufficient_data').
4. Mixed / Drifting User Resilience (gracefully handles drifting profiles).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from ml.models.behavior_classifier import BehaviorClassifier
from ml.training.dataset import load_dataset


def run_scale_invariance_test(
    classifier: BehaviorClassifier, df_samples: pd.DataFrame
) -> tuple[bool, float]:
    """Test that multiplying currency amounts by 2 preserves identical predicted profile."""
    print("\n--- 1. Scale Invariance Check ---")
    total = min(len(df_samples), 500)
    subset = df_samples.iloc[:total]

    base_dicts = [row.to_dict() for _, row in subset.iterrows()]
    scaled_dicts = []

    for d in base_dicts:
        s = dict(d)
        s["income"] = float(d.get("income", 0.0)) * 2.0
        s["expense"] = float(d.get("expense", 0.0)) * 2.0
        s["savings"] = float(d.get("savings", 0.0)) * 2.0
        s["necessity_expense"] = float(d.get("necessity_expense", 0.0)) * 2.0
        s["discretionary_expense"] = float(d.get("discretionary_expense", 0.0)) * 2.0
        s["avg_txn"] = float(d.get("avg_txn", 1.0)) * 2.0
        s["expense_variance"] = float(d.get("expense_variance", 0.0)) * 4.0
        s["rolling_expense_3m_mean"] = float(d.get("rolling_expense_3m_mean", 1.0)) * 2.0
        s["spending_trend_3m"] = float(d.get("spending_trend_3m", 0.0)) * 2.0
        scaled_dicts.append(s)

    preds_base = classifier.predict_batch(base_dicts, months_active=12)
    preds_scaled = classifier.predict_batch(scaled_dicts, months_active=12)

    identical_count = sum(
        1
        for p1, p2 in zip(preds_base, preds_scaled, strict=False)
        if p1.profile == p2.profile and abs(p1.confidence - p2.confidence) < 1e-4
    )

    ratio = identical_count / total
    passed = ratio == 1.0
    print(f"  * Scale Invariance Consistency: {ratio * 100:.2f}% ({identical_count}/{total})")
    print(f"  * Status: {'[PASS]' if passed else '[FAIL]'}")
    return passed, ratio


def run_noise_injection_test(
    classifier: BehaviorClassifier, df_samples: pd.DataFrame
) -> tuple[bool, float]:
    """Test label stability under +/- 5% Gaussian noise injection."""
    print("\n--- 2. Noise Perturbation Tolerance Check ---")
    total = min(len(df_samples), 500)
    subset = df_samples.iloc[:total]

    rng = np.random.RandomState(42)
    base_dicts = [row.to_dict() for _, row in subset.iterrows()]
    noisy_dicts = []

    for d in base_dicts:
        noisy = dict(d)
        for key in ["savings_rate", "necessity_rate", "discretionary_rate", "income_expense_ratio"]:
            val = float(d.get(key) or 0.0)
            noise = rng.normal(0.0, 0.05 * max(val, 0.05))
            noisy[key] = max(0.0, val + noise)
        noisy_dicts.append(noisy)

    preds_base = classifier.predict_batch(base_dicts, months_active=12)
    preds_noisy = classifier.predict_batch(noisy_dicts, months_active=12)

    consistent_count = sum(
        1 for p1, p2 in zip(preds_base, preds_noisy, strict=False) if p1.profile == p2.profile
    )

    ratio = consistent_count / total
    passed = ratio >= 0.90
    print(f"  * Noise Stability Rate: {ratio * 100:.2f}% (Threshold >= 90.0%)")
    print(f"  * Status: {'[PASS]' if passed else '[FAIL]'}")
    return passed, ratio


def run_cold_start_test(classifier: BehaviorClassifier) -> bool:
    """Test that users with < 2 months of activity receive 'insufficient_data'."""
    print("\n--- 3. Cold-Start Policy Check ---")
    sample_features = {
        "savings_rate": 0.25,
        "necessity_rate": 0.60,
        "discretionary_rate": 0.15,
        "txn_count": 10,
        "cashout_count": 2,
    }

    p0 = classifier.predict(sample_features, months_active=0)
    p1 = classifier.predict(sample_features, months_active=1)
    p2 = classifier.predict(sample_features, months_active=2)

    c0_ok = p0.profile == "insufficient_data" and p0.is_cold_start and p0.confidence == 0.0
    c1_ok = p1.profile == "insufficient_data" and p1.is_cold_start and p1.confidence == 0.0
    c2_ok = p2.profile != "insufficient_data" and not p2.is_cold_start and p2.confidence > 0.0

    passed = c0_ok and c1_ok and c2_ok
    print(f"  * Months Active = 0: profile = '{p0.profile}', is_cold_start = {p0.is_cold_start}")
    print(f"  * Months Active = 1: profile = '{p1.profile}', is_cold_start = {p1.is_cold_start}")
    print(f"  * Months Active = 2: profile = '{p2.profile}', is_cold_start = {p2.is_cold_start}")
    print(f"  * Status: {'[PASS]' if passed else '[FAIL]'}")
    return passed


def run_drifting_users_resilience_test(
    classifier: BehaviorClassifier, data_dir: Path | str
) -> tuple[bool, int]:
    """Test that mixed/drifting users produce valid predictions and calibrated confidences without errors."""
    print("\n--- 4. Mixed / Drifting Users Resilience Check ---")
    _, _, _, df_all, _ = load_dataset(data_dir, exclude_drifting=False)
    drifting_df = df_all[df_all["true_persona"] == "mixed_drifting"]
    print(f"  * Found {len(drifting_df)} monthly records for mixed/drifting users.")

    records = [row.to_dict() for _, row in drifting_df.iterrows()]
    predictions = classifier.predict_batch(records, months_active=12)

    error_count = sum(
        1 for p in predictions if not p.profile or p.confidence <= 0.0 or not p.top_factors
    )

    passed = error_count == 0 and len(predictions) > 0
    print(f"  * Successfully processed: {len(predictions)}/{len(drifting_df)} records")
    print(
        f"  * Mean Confidence on Drifting Users: {np.mean([p.confidence for p in predictions]):.4f}"
    )
    print(f"  * Status: {'[PASS]' if passed else '[FAIL]'}")
    return passed, len(predictions)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run robustness tests for Behavior Classifier")
    parser.add_argument("--data-dir", default="data/exports", help="Dataset directory")
    args = parser.parse_args()

    model_path = Path("ml/artifacts/behavior_classifier_v1.joblib")
    meta_path = Path("ml/artifacts/behavior_classifier_v1_metadata.json")

    print("=" * 70)
    print("      SOHOJ ML MODEL A: ROBUSTNESS & INVARIANCE VALIDATION")
    print("=" * 70)

    clf = BehaviorClassifier.load(model_path, meta_path)
    print(
        f"[+] Loaded verified model version {clf.model_version} with SHA-256 {clf.sha256_checksum[:16]}..."
    )

    _, _, _, df_train, _ = load_dataset(args.data_dir, exclude_drifting=True)

    t1_pass, _ = run_scale_invariance_test(clf, df_train)
    t2_pass, _ = run_noise_injection_test(clf, df_train)
    t3_pass = run_cold_start_test(clf)
    t4_pass, _ = run_drifting_users_resilience_test(clf, args.data_dir)

    all_passed = t1_pass and t2_pass and t3_pass and t4_pass
    print("\n" + "=" * 70)
    if all_passed:
        print(">>> ALL ROBUSTNESS CHECKS PASSED SUCCESSFULLY! <<<")
        return 0
    else:
        print(">>> ONE OR MORE ROBUSTNESS CHECKS FAILED! <<<")
        return 1


if __name__ == "__main__":
    sys.exit(main())
