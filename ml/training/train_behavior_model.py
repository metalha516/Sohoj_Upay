"""Model A (Behavior Classification) Training, Calibration, Evaluation, and Packaging Pipeline.

Covers:
1. Model ladder benchmark: Rule Baseline -> Logistic Regression -> Random Forest -> Gradient Boosting (HGB / LightGBM-architecture).
2. 5-Fold StratifiedGroupKFold on user_id to prevent user-level data leakage.
3. Probability calibration via CalibratedClassifierCV(method='sigmoid').
4. Comprehensive evaluation on held-out seed cohort (Accuracy, Macro-F1, ROC-AUC, ECE, Confusion Matrix).
5. Explainability with permutation feature importances and human-readable factor generation.
6. Checksum-verified model artifact packaging.
7. Diagnostic plot generation.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelBinarizer, StandardScaler

from ml.models.baselines import RuleBasedBehaviorClassifier
from ml.training.dataset import (
    FEATURE_NAMES,
    compute_file_sha256,
    load_dataset,
)


def get_git_sha() -> str:
    """Retrieve current git commit hash."""
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"


def compute_ece(
    y_true: np.ndarray, y_prob: np.ndarray, classes: np.ndarray, n_bins: int = 10
) -> tuple[float, list[dict[str, float]]]:
    """Calculate Expected Calibration Error (ECE) across confidence bins."""
    y_pred = classes[np.argmax(y_prob, axis=1)]
    confidences = np.max(y_prob, axis=1)
    accuracies = (y_pred == y_true).astype(float)

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    bin_details = []

    for i in range(n_bins):
        b_low, b_high = bin_boundaries[i], bin_boundaries[i + 1]
        in_bin = (
            (confidences > b_low) & (confidences <= b_high)
            if i > 0
            else (confidences >= b_low) & (confidences <= b_high)
        )
        count = int(np.sum(in_bin))

        if count > 0:
            bin_acc = float(np.mean(accuracies[in_bin]))
            bin_conf = float(np.mean(confidences[in_bin]))
            weight = count / len(y_true)
            ece += weight * abs(bin_acc - bin_conf)
            bin_details.append(
                {
                    "bin_lower": round(float(b_low), 2),
                    "bin_upper": round(float(b_high), 2),
                    "count": count,
                    "accuracy": round(bin_acc, 4),
                    "confidence": round(bin_conf, 4),
                }
            )

    return float(round(ece, 4)), bin_details


def run_model_comparison_cv(
    X: np.ndarray, y: np.ndarray, groups: np.ndarray, df_merged: pd.DataFrame
) -> dict[str, dict[str, float]]:
    """Run 5-Fold StratifiedGroupKFold to benchmark model ladder."""
    print("\n[*] Running 5-Fold Stratified User-Group Cross-Validation...")
    sgkf = StratifiedGroupKFold(n_splits=5)

    rule_clf = RuleBasedBehaviorClassifier()
    scores: dict[str, dict[str, list[float]]] = {
        "rule_baseline": {"f1": [], "acc": []},
        "logistic_regression": {"f1": [], "acc": []},
        "random_forest": {"f1": [], "acc": []},
        "hist_gradient_boosting": {"f1": [], "acc": []},
        "calibrated_gradient_boosting": {"f1": [], "acc": []},
    }

    for fold, (train_idx, val_idx) in enumerate(sgkf.split(X, y, groups), start=1):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        val_df = df_merged.iloc[val_idx]

        # 1. Rule Baseline
        rule_preds = []
        for _, row in val_df.iterrows():
            txn_cnt = max(float(row.get("txn_count") or 1.0), 1.0)
            c_cnt = float(row.get("cashout_count") or 0.0)
            avg_t = max(float(row.get("avg_txn") or 1.0), 1.0)
            var_t = max(float(row.get("expense_variance") or 0.0), 0.0)
            pred_profile = rule_clf.predict(
                savings_rate=float(row.get("savings_rate") or 0.0),
                cashout_ratio=c_cnt / txn_cnt,
                cashout_count=c_cnt,
                necessity_share=float(row.get("necessity_rate") or 0.0),
                discretionary_share=float(row.get("discretionary_rate") or 0.0),
                volatility_cv=float(np.sqrt(var_t) / avg_t),
                months_active=12,
            ).profile
            rule_preds.append(pred_profile)

        scores["rule_baseline"]["f1"].append(f1_score(y_val, rule_preds, average="macro"))
        scores["rule_baseline"]["acc"].append(accuracy_score(y_val, rule_preds))

        # 2. Logistic Regression
        lr_pipe = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=1000, random_state=42)),
            ]
        )
        lr_pipe.fit(X_train, y_train)
        lr_preds = lr_pipe.predict(X_val)
        scores["logistic_regression"]["f1"].append(f1_score(y_val, lr_preds, average="macro"))
        scores["logistic_regression"]["acc"].append(accuracy_score(y_val, lr_preds))

        # 3. Random Forest
        rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        rf_preds = rf.predict(X_val)
        scores["random_forest"]["f1"].append(f1_score(y_val, rf_preds, average="macro"))
        scores["random_forest"]["acc"].append(accuracy_score(y_val, rf_preds))

        # 4. Hist Gradient Boosting (LightGBM-architecture)
        hgb = HistGradientBoostingClassifier(
            max_iter=120,
            learning_rate=0.05,
            max_leaf_nodes=31,
            random_state=42,
        )
        hgb.fit(X_train, y_train)
        hgb_preds = hgb.predict(X_val)
        scores["hist_gradient_boosting"]["f1"].append(f1_score(y_val, hgb_preds, average="macro"))
        scores["hist_gradient_boosting"]["acc"].append(accuracy_score(y_val, hgb_preds))

        # 5. Calibrated Gradient Boosting
        hgb_base = HistGradientBoostingClassifier(
            max_iter=120,
            learning_rate=0.05,
            max_leaf_nodes=31,
            random_state=42,
        )
        cal_clf = CalibratedClassifierCV(estimator=hgb_base, method="sigmoid", cv=3)
        cal_clf.fit(X_train, y_train)
        cal_preds = cal_clf.predict(X_val)
        scores["calibrated_gradient_boosting"]["f1"].append(
            f1_score(y_val, cal_preds, average="macro")
        )
        scores["calibrated_gradient_boosting"]["acc"].append(accuracy_score(y_val, cal_preds))

        print(
            f"    - Fold {fold}/5: Calibrated HGB Macro-F1 = {scores['calibrated_gradient_boosting']['f1'][-1]:.4f}"
        )

    summary = {}
    for model_name, metrics in scores.items():
        summary[model_name] = {
            "macro_f1_mean": float(round(np.mean(metrics["f1"]), 4)),
            "macro_f1_std": float(round(np.std(metrics["f1"]), 4)),
            "accuracy_mean": float(round(np.mean(metrics["acc"]), 4)),
            "accuracy_std": float(round(np.std(metrics["acc"]), 4)),
        }
        print(
            f"  * {model_name:30s}: Macro-F1 = {summary[model_name]['macro_f1_mean']:.4f} (+/- {summary[model_name]['macro_f1_std']:.4f}) | Acc = {summary[model_name]['accuracy_mean']:.4f}"
        )

    return summary


def train_calibrated_model(
    X: np.ndarray, y: np.ndarray
) -> tuple[CalibratedClassifierCV, HistGradientBoostingClassifier]:
    """Train the final production CalibratedClassifierCV over HistGradientBoosting."""
    print("\n[*] Training final production CalibratedClassifierCV on primary dataset...")
    base_clf = HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.05,
        max_leaf_nodes=31,
        random_state=42,
    )
    base_clf.fit(X, y)

    calibrated_model = CalibratedClassifierCV(
        estimator=HistGradientBoostingClassifier(
            max_iter=150,
            learning_rate=0.05,
            max_leaf_nodes=31,
            random_state=42,
        ),
        method="sigmoid",
        cv=5,
    )
    calibrated_model.fit(X, y)
    return calibrated_model, base_clf


def evaluate_on_heldout(
    model: CalibratedClassifierCV,
    X_held: np.ndarray,
    y_held: np.ndarray,
    output_dir: Path,
) -> dict[str, Any]:
    """Evaluate calibrated model on quarantined held-out seed cohort."""
    print("\n[*] Evaluating on Quarantined Held-Out Seed Dataset...")
    classes = model.classes_
    y_pred = model.predict(X_held)
    y_prob = model.predict_proba(X_held)

    acc = float(accuracy_score(y_held, y_pred))
    macro_f1 = float(f1_score(y_held, y_pred, average="macro"))
    weighted_f1 = float(f1_score(y_held, y_pred, average="weighted"))

    # Binarize labels for multi-class ROC-AUC (One-vs-Rest)
    lb = LabelBinarizer()
    lb.fit(classes)
    y_held_bin = lb.transform(y_held)
    roc_auc_ovr = float(roc_auc_score(y_held_bin, y_prob, multi_class="ovr", average="macro"))

    # Expected Calibration Error
    ece, ece_bins = compute_ece(y_held, y_prob, classes)

    # Classification report dict
    clf_report = classification_report(y_held, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_held, y_pred, labels=classes)

    print(f"  * Held-Out Accuracy:    {acc:.4f}")
    print(f"  * Held-Out Macro-F1:    {macro_f1:.4f}")
    print(f"  * Held-Out ROC-AUC OvR: {roc_auc_ovr:.4f}")
    print(f"  * Held-Out ECE:         {ece:.4f}")

    # Generate diagnostic plots
    fig_dir = output_dir / "docs" / "ml" / "figures" / "model_a"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. Confusion Matrix Plot
    plt.figure(figsize=(9, 7))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=classes,
        yticklabels=classes,
    )
    plt.title(f"Model A Confusion Matrix on Held-Out Cohort (Macro-F1 = {macro_f1:.3f})")
    plt.xlabel("Predicted Profile")
    plt.ylabel("Ground Truth Profile")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    cm_path = fig_dir / "confusion_matrix.png"
    plt.savefig(cm_path, dpi=300)
    plt.close()

    # 2. Calibration Curve Plot
    plt.figure(figsize=(8, 6))
    for i, cls_name in enumerate(classes):
        prob_true, prob_pred = calibration_curve(y_held_bin[:, i], y_prob[:, i], n_bins=10)
        plt.plot(prob_pred, prob_true, marker="o", label=cls_name)
    plt.plot([0, 1], [0, 1], "k--", label="Perfect Calibration")
    plt.title(f"Reliability Diagram (Calibration Curve) — ECE = {ece:.3f}")
    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("Fraction of Positives")
    plt.legend(loc="upper left", fontsize=8)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    cal_path = fig_dir / "calibration_curve.png"
    plt.savefig(cal_path, dpi=300)
    plt.close()

    # 3. ROC Curves Plot
    plt.figure(figsize=(8, 6))
    for i, cls_name in enumerate(classes):
        fpr, tpr, _ = roc_curve(y_held_bin[:, i], y_prob[:, i])
        plt.plot(
            fpr,
            tpr,
            label=f"{cls_name} (AUC = {roc_auc_score(y_held_bin[:, i], y_prob[:, i]):.3f})",
        )
    plt.plot([0, 1], [0, 1], "k--", label="Random Chance")
    plt.title(f"One-vs-Rest ROC Curves (Macro ROC-AUC = {roc_auc_ovr:.3f})")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend(loc="lower right", fontsize=8)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    roc_path = fig_dir / "roc_auc_curve.png"
    plt.savefig(roc_path, dpi=300)
    plt.close()

    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "roc_auc_ovr": roc_auc_ovr,
        "ece": ece,
        "ece_bins": ece_bins,
        "classification_report": clf_report,
        "confusion_matrix": cm.tolist(),
        "classes": classes.tolist(),
        "figures": {
            "confusion_matrix": str(cm_path),
            "calibration_curve": str(cal_path),
            "roc_auc_curve": str(roc_path),
        },
    }


def compute_feature_importance_plot(
    base_clf: HistGradientBoostingClassifier,
    X: np.ndarray,
    y: np.ndarray,
    output_dir: Path,
) -> list[dict[str, Any]]:
    """Compute permutation feature importance across features."""
    print("\n[*] Computing permutation feature importance...")
    # Sample 1000 points for speed
    n_pts = min(1000, len(X))
    idx = np.random.RandomState(42).choice(len(X), size=n_pts, replace=False)
    perm_res = permutation_importance(
        base_clf, X[idx], y[idx], n_repeats=5, random_state=42, n_jobs=-1
    )
    mean_imp = perm_res.importances_mean

    sorted_idx = np.argsort(mean_imp)[::-1]
    factors = []
    for i in sorted_idx:
        factors.append(
            {
                "feature": FEATURE_NAMES[i],
                "importance": float(round(mean_imp[i], 4)),
            }
        )

    fig_dir = output_dir / "docs" / "ml" / "figures" / "model_a"
    fig_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(9, 6))
    ordered_feats = [FEATURE_NAMES[i] for i in sorted_idx][::-1]
    ordered_scores = [mean_imp[i] for i in sorted_idx][::-1]
    plt.barh(ordered_feats, ordered_scores, color="#1976D2")
    plt.title("Model A Permutation Feature Importance")
    plt.xlabel("Mean Accuracy Decrease Upon Shuffling")
    plt.tight_layout()
    imp_path = fig_dir / "feature_importance.png"
    plt.savefig(imp_path, dpi=300)
    plt.close()

    return factors


def save_versioned_artifact(
    model: CalibratedClassifierCV,
    base_clf: HistGradientBoostingClassifier,
    cv_summary: dict[str, Any],
    heldout_eval: dict[str, Any],
    feature_importances: list[dict[str, Any]],
    dataset_hash: str,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Serialize model artifact with SHA-256 checksum and metadata."""
    artifact_dir = output_dir / "ml" / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    model_file = artifact_dir / "behavior_classifier_v1.joblib"
    meta_file = artifact_dir / "behavior_classifier_v1_metadata.json"

    # Save model package
    package = {
        "calibrated_model": model,
        "base_estimator": base_clf,
        "feature_names": FEATURE_NAMES,
        "classes": model.classes_.tolist(),
        "model_version": "v1.0.0",
        "feature_schema_version": "v1.0.0",
    }
    joblib.dump(package, model_file, compress=3)

    # Compute SHA-256 checksum
    checksum = compute_file_sha256(model_file)

    metadata = {
        "model_name": "behavior_classifier",
        "model_version": "v1.0.0",
        "feature_schema_version": "v1.0.0",
        "feature_names": FEATURE_NAMES,
        "classes": model.classes_.tolist(),
        "dataset_hash": dataset_hash,
        "git_sha": get_git_sha(),
        "created_at": datetime.now(UTC).isoformat(),
        "sha256_checksum": checksum,
        "cv_benchmarks": cv_summary,
        "heldout_metrics": {
            "accuracy": heldout_eval["accuracy"],
            "macro_f1": heldout_eval["macro_f1"],
            "weighted_f1": heldout_eval["weighted_f1"],
            "roc_auc_ovr": heldout_eval["roc_auc_ovr"],
            "ece": heldout_eval["ece"],
        },
        "feature_importances": feature_importances,
    }

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\n[+] Saved versioned model artifact:")
    print(f"    - Model:    {model_file}")
    print(f"    - Metadata: {meta_file}")
    print(f"    - SHA-256:  {checksum}")

    return model_file, meta_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Train and evaluate Behavior Classifier Model A")
    parser.add_argument("--data-dir", default="data/exports", help="Primary data directory")
    parser.add_argument(
        "--heldout-dir", default="data/exports/held_out", help="Held-out data directory"
    )
    parser.add_argument("--output-dir", default=".", help="Root output directory")
    args = parser.parse_args()

    root = Path(args.output_dir)
    print("=" * 70)
    print("       SOHOJ ML MODEL A: BEHAVIOR CLASSIFICATION PIPELINE")
    print("=" * 70)

    # 1. Load Primary Dataset
    X_train, y_train, groups_train, df_train, train_hash = load_dataset(
        args.data_dir, exclude_drifting=True
    )
    print(
        f"[+] Loaded primary dataset: {X_train.shape[0]:,} samples, 14 features across {len(np.unique(groups_train))} users."
    )

    # 2. Run Model Comparison Cross-Validation
    cv_summary = run_model_comparison_cv(X_train, y_train, groups_train, df_train)

    # 3. Train Final Calibrated Model
    calibrated_model, base_clf = train_calibrated_model(X_train, y_train)

    # 4. Load Held-Out Quarantined Dataset
    X_held, y_held, groups_held, df_held, held_hash = load_dataset(
        args.heldout_dir, exclude_drifting=True
    )
    print(
        f"[+] Loaded held-out seed dataset: {X_held.shape[0]:,} samples across {len(np.unique(groups_held))} users."
    )

    # 5. Evaluate on Held-Out Dataset
    heldout_eval = evaluate_on_heldout(calibrated_model, X_held, y_held, root)

    # 6. Feature Importance
    feature_importances = compute_feature_importance_plot(base_clf, X_train, y_train, root)

    # 7. Save Versioned Artifact
    save_versioned_artifact(
        calibrated_model,
        base_clf,
        cv_summary,
        heldout_eval,
        feature_importances,
        train_hash,
        root,
    )

    print("\n[+] Model A training and evaluation pipeline completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
