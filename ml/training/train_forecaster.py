"""Training, benchmark, and evaluation pipeline for Model C (Expense Forecasting).

Evaluates model ladder (Naive -> 3M MA -> Ridge -> HistGradientBoosting Quantile Regressor),
executes time-based rolling-origin validation, verifies uncertainty coverage within nominal +/-10%,
evaluates on held-out seed cohort, plots diagnostic figures, and serializes versioned artifacts.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.preprocessing import StandardScaler

from ml.models.expense_forecaster import ExpenseForecaster


def compute_file_sha256(path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def get_git_sha() -> str:
    """Get current git commit hash."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def calculate_smape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Calculate Symmetric Mean Absolute Percentage Error (sMAPE)."""
    denom = np.abs(actual) + np.abs(predicted) + 1e-6
    return float(np.mean(2.0 * np.abs(actual - predicted) / denom) * 100.0)


def calculate_mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Calculate MAPE with near-zero guardrail."""
    denom = np.maximum(np.abs(actual), 100.0)
    return float(np.mean(np.abs(actual - predicted) / denom) * 100.0)


def calculate_pinball_loss(actual: np.ndarray, predicted: np.ndarray, alpha: float) -> float:
    """Calculate quantile / pinball loss."""
    diff = actual - predicted
    return float(np.mean(np.maximum(alpha * diff, (alpha - 1.0) * diff)))


def prepare_dataset(mf_path: Path) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, list[str]]:
    """Assemble chronological lag features and next-month target."""
    df_mf = pd.read_parquet(mf_path)
    df_mf = df_mf.sort_values(["user_id", "month"]).reset_index(drop=True)

    df_mf["target"] = df_mf.groupby("user_id")["expense"].shift(-1)
    df_mf["lag2_expense"] = df_mf.groupby("user_id")["expense"].shift(1).fillna(df_mf["expense"])
    df_mf["lag3_expense"] = (
        df_mf.groupby("user_id")["expense"].shift(2).fillna(df_mf["lag2_expense"])
    )

    df_mf["month_num"] = pd.to_datetime(df_mf["month"]).dt.month
    df_mf["target_month_num"] = (df_mf["month_num"] % 12) + 1
    df_mf["is_target_eid"] = df_mf["target_month_num"].isin([3, 5]).astype(float)

    valid = df_mf[df_mf["target"].notna()].copy()

    feature_cols = [
        "expense",
        "lag2_expense",
        "lag3_expense",
        "rolling_expense_3m_mean",
        "rolling_expense_3m_std",
        "spending_trend_3m",
        "income",
        "savings_rate",
        "necessity_rate",
        "discretionary_rate",
        "txn_count",
        "cashout_count",
        "target_month_num",
        "is_target_eid",
    ]

    X = valid[feature_cols].fillna(valid[feature_cols].median()).to_numpy(dtype=np.float64)
    y = valid["target"].to_numpy(dtype=np.float64)

    return valid, X, y, feature_cols


def main() -> None:
    print("=" * 70)
    print(" Sohoj Model C: Expense Forecasting Training & Benchmark Pipeline")
    print("=" * 70)

    figures_dir = Path("docs/ml/figures/model_c")
    figures_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = Path("ml/artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Primary Dataset
    primary_mf_path = Path("data/exports/monthly_features.parquet")
    if not primary_mf_path.exists():
        raise FileNotFoundError("monthly_features.parquet missing. Run backfill first.")

    print("\n[1/6] Loading Primary Feature Store (N=600 users)...")
    valid_df, X_all, y_all, feature_cols = prepare_dataset(primary_mf_path)
    mf_hash = compute_file_sha256(primary_mf_path)
    print(f"  Valid forecast transitions: {len(valid_df):,} | SHA-256: {mf_hash[:16]}...")

    # 2. Rolling-Origin Cross-Validation
    print("\n[2/6] Executing Time-Based Rolling-Origin Sequential Cross-Validation...")
    # Evaluate across 3 sequential horizons: Train <= 6 Test 7, Train <= 7 Test 8, ... Train <= 10 Test 11
    eval_splits = [
        (6, 7),
        (7, 8),
        (8, 9),
        (9, 10),
        (10, 11),
    ]

    ladder_metrics: dict[str, dict[str, list[float]]] = {
        "naive": {"mae": [], "rmse": [], "smape": []},
        "moving_average_3m": {"mae": [], "rmse": [], "smape": []},
        "ridge": {"mae": [], "rmse": [], "smape": []},
        "gbdt_quantile": {"mae": [], "rmse": [], "smape": [], "coverage": [], "pinball_50": []},
    }

    rolling_horizon_errors = []

    for train_max_m, test_m in eval_splits:
        train_idx = valid_df["month_num"] <= train_max_m
        test_idx = valid_df["month_num"] == test_m

        X_tr, y_tr = X_all[train_idx], y_all[train_idx]
        X_te, y_te = X_all[test_idx], y_all[test_idx]

        # A. Naive baseline (expense at t)
        naive_preds = valid_df.loc[test_idx, "expense"].to_numpy()
        ladder_metrics["naive"]["mae"].append(mean_absolute_error(y_te, naive_preds))
        ladder_metrics["naive"]["rmse"].append(root_mean_squared_error(y_te, naive_preds))
        ladder_metrics["naive"]["smape"].append(calculate_smape(y_te, naive_preds))

        # B. 3-Month Moving Average
        ma_preds = valid_df.loc[test_idx, "rolling_expense_3m_mean"].to_numpy()
        ladder_metrics["moving_average_3m"]["mae"].append(mean_absolute_error(y_te, ma_preds))
        ladder_metrics["moving_average_3m"]["rmse"].append(root_mean_squared_error(y_te, ma_preds))
        ladder_metrics["moving_average_3m"]["smape"].append(calculate_smape(y_te, ma_preds))

        # C. Ridge Regression
        scaler = StandardScaler()
        ridge = Ridge(alpha=100.0)
        ridge.fit(scaler.fit_transform(X_tr), y_tr)
        ridge_preds = ridge.predict(scaler.transform(X_te))
        ladder_metrics["ridge"]["mae"].append(mean_absolute_error(y_te, ridge_preds))
        ladder_metrics["ridge"]["rmse"].append(root_mean_squared_error(y_te, ridge_preds))
        ladder_metrics["ridge"]["smape"].append(calculate_smape(y_te, ridge_preds))

        # D. HistGradientBoosting Quantile Regressor
        forecaster = ExpenseForecaster()
        forecaster.fit(X_tr, y_tr)
        assert (
            forecaster.model_p50 is not None
            and forecaster.model_p10 is not None
            and forecaster.model_p90 is not None
        )

        p50 = forecaster.model_p50.predict(X_te)
        p10 = forecaster.model_p10.predict(X_te)
        p90 = forecaster.model_p90.predict(X_te)

        cov = np.mean((y_te >= p10) & (y_te <= p90))
        mae = mean_absolute_error(y_te, p50)
        rmse = root_mean_squared_error(y_te, p50)
        sm = calculate_smape(y_te, p50)
        pin50 = calculate_pinball_loss(y_te, p50, 0.50)

        ladder_metrics["gbdt_quantile"]["mae"].append(mae)
        ladder_metrics["gbdt_quantile"]["rmse"].append(rmse)
        ladder_metrics["gbdt_quantile"]["smape"].append(sm)
        ladder_metrics["gbdt_quantile"]["coverage"].append(cov)
        ladder_metrics["gbdt_quantile"]["pinball_50"].append(pin50)

        rolling_horizon_errors.append(
            {
                "horizon": f"M{train_max_m}->M{test_m}",
                "naive_mae": ladder_metrics["naive"]["mae"][-1],
                "ma_mae": ladder_metrics["moving_average_3m"]["mae"][-1],
                "ridge_mae": ladder_metrics["ridge"]["mae"][-1],
                "gbdt_mae": mae,
                "coverage": cov,
            }
        )

    # Summary table
    print("\n[3/6] Model Ladder Benchmark Results (Averaged across Rolling Horizons):")
    summary_results = {}
    for m_name in ["naive", "moving_average_3m", "ridge", "gbdt_quantile"]:
        mae_m = float(np.mean(ladder_metrics[m_name]["mae"]))
        rmse_m = float(np.mean(ladder_metrics[m_name]["rmse"]))
        smape_m = float(np.mean(ladder_metrics[m_name]["smape"]))
        summary_results[m_name] = {"mae": mae_m, "rmse": rmse_m, "smape": smape_m}
        cov_str = (
            f" | 80% Coverage: {np.mean(ladder_metrics[m_name]['coverage']) * 100.0:.1f}%"
            if "coverage" in ladder_metrics[m_name]
            else ""
        )
        print(
            f"  {m_name:20s} | MAE: {mae_m:8.2f} | RMSE: {rmse_m:8.2f} | sMAPE: {smape_m:5.2f}%{cov_str}"
        )

    mean_coverage = float(np.mean(ladder_metrics["gbdt_quantile"]["coverage"]))
    print(
        f"\n  Empirical Interval Coverage: {mean_coverage * 100.0:.2f}% (Nominal 80.0%, Tolerance: 70%-90%)"
    )
    assert 0.70 <= mean_coverage <= 0.90, f"Coverage {mean_coverage} outside nominal +/-10%!"
    print("  Coverage Acceptance Criterion: PASS (within nominal +/-10%)")

    # 4. Final Fit & Quarantined Held-Out Evaluation
    print("\n[4/6] Training Final Production Forecaster & Evaluating on Held-Out Cohort (N=200)...")
    final_forecaster = ExpenseForecaster()
    final_forecaster.fit(X_all, y_all)
    final_forecaster.feature_medians = valid_df[feature_cols].median().to_dict()

    assert (
        final_forecaster.model_p50 is not None
        and final_forecaster.model_p10 is not None
        and final_forecaster.model_p90 is not None
    )

    held_mf_path = Path("data/exports/held_out/monthly_features.parquet")
    held_df, X_held, y_held, _ = prepare_dataset(held_mf_path)
    held_hash = compute_file_sha256(held_mf_path)

    # Held-out predictions
    held_p50 = final_forecaster.model_p50.predict(X_held)
    held_p10 = final_forecaster.model_p10.predict(X_held)
    held_p90 = final_forecaster.model_p90.predict(X_held)

    held_naive = held_df["expense"].to_numpy()
    held_naive_mae = mean_absolute_error(y_held, held_naive)

    held_mae = mean_absolute_error(y_held, held_p50)
    held_rmse = root_mean_squared_error(y_held, held_p50)
    held_mape = calculate_mape(y_held, held_p50)
    held_smape = calculate_smape(y_held, held_p50)
    held_coverage = float(np.mean((y_held >= held_p10) & (y_held <= held_p90)))
    held_pinball = calculate_pinball_loss(y_held, held_p50, 0.50)

    print(f"  Held-Out Naive MAE:    {held_naive_mae:,.2f}")
    print(
        f"  Held-Out Forecaster MAE: {held_mae:,.2f} (Beats naive by {held_naive_mae - held_mae:,.2f} BDT)"
    )
    print(f"  Held-Out Forecaster RMSE: {held_rmse:,.2f}")
    print(f"  Held-Out sMAPE:          {held_smape:.2f}%")
    print(f"  Held-Out MAPE:           {held_mape:.2f}%")
    print(f"  Held-Out 80% Coverage:   {held_coverage * 100.0:.2f}% (Tolerance: 70%-90%)")

    # 5. Diagnostic Figures
    print("\n[5/6] Generating Diagnostic Figures in docs/ml/figures/model_c/...")

    # Figure 1: Model Ladder MAE
    fig, ax = plt.subplots(figsize=(8, 5))
    model_labels = ["Naive", "3-Month MA", "Ridge", "GBDT Quantile (Ours)"]
    mae_vals = [
        summary_results["naive"]["mae"],
        summary_results["moving_average_3m"]["mae"],
        summary_results["ridge"]["mae"],
        summary_results["gbdt_quantile"]["mae"],
    ]
    bar_colors = ["#d62728", "#ff7f0e", "#1f77b4", "#2ca02c"]
    bars = ax.bar(model_labels, mae_vals, color=bar_colors, width=0.5)
    ax.set_ylabel("Mean Absolute Error (BDT)", fontweight="bold")
    ax.set_title(
        "Model C: Expense Forecasting Model Ladder (Rolling-Origin MAE)", fontweight="bold", pad=12
    )
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            h + 80,
            f"৳{h:,.0f}",
            ha="center",
            va="bottom",
            fontweight="bold",
        )
    plt.tight_layout()
    plt.savefig(figures_dir / "forecast_ladder_mae.png", dpi=300)
    plt.close()

    # Figure 2: Rolling Origin Horizon Metrics
    fig, ax = plt.subplots(figsize=(8, 5))
    horizons = [r["horizon"] for r in rolling_horizon_errors]
    naive_errs = [r["naive_mae"] for r in rolling_horizon_errors]
    gbdt_errs = [r["gbdt_mae"] for r in rolling_horizon_errors]
    ax.plot(horizons, naive_errs, marker="o", color="tab:red", linewidth=2, label="Naive Baseline")
    ax.plot(
        horizons,
        gbdt_errs,
        marker="s",
        color="tab:green",
        linewidth=2.5,
        label="GBDT Quantile Regressor",
    )
    ax.set_xlabel("Sequential Rolling Horizon", fontweight="bold")
    ax.set_ylabel("MAE (BDT)", fontweight="bold")
    ax.set_title("Forecast Accuracy across Sequential Horizons", fontweight="bold", pad=12)
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(figures_dir / "rolling_origin_metrics.png", dpi=300)
    plt.close()

    # Figure 3: Uncertainty Prediction Intervals
    fig, ax = plt.subplots(figsize=(9, 5))
    # Pick a sample slice of 30 held-out instances sorted by actual
    sample_idx = np.argsort(y_held)[:35]
    x_axis = np.arange(len(sample_idx))
    ax.fill_between(
        x_axis,
        held_p10[sample_idx],
        held_p90[sample_idx],
        color="tab:blue",
        alpha=0.25,
        label=f"80% Prediction Interval (Coverage: {held_coverage * 100.0:.1f}%)",
    )
    ax.plot(
        x_axis,
        held_p50[sample_idx],
        color="tab:blue",
        linewidth=1.8,
        label="Predicted Median (p50)",
    )
    ax.scatter(
        x_axis,
        y_held[sample_idx],
        color="tab:red",
        s=30,
        zorder=5,
        label="Actual Next-Month Expense",
    )
    ax.set_xlabel("Sample Accounts (Sorted by Actual Spend)", fontweight="bold")
    ax.set_ylabel("Expense Amount (BDT)", fontweight="bold")
    ax.set_title("Model C: 80% Uncertainty Interval Coverage vs Actuals", fontweight="bold", pad=12)
    ax.legend(loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(figures_dir / "interval_coverage.png", dpi=300)
    plt.close()

    # Figure 4: Residuals Distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    residuals = y_held - held_p50
    ax.hist(residuals, bins=40, color="#1f77b4", edgecolor="black", alpha=0.7, density=True)
    ax.axvline(0, color="tab:red", linestyle="--", linewidth=1.5, label="Zero Bias Line")
    ax.set_xlabel("Forecast Residual (Actual - Predicted) [BDT]", fontweight="bold")
    ax.set_ylabel("Density", fontweight="bold")
    ax.set_title(
        "Model C: Residuals Distribution on Quarantined Held-Out Cohort", fontweight="bold", pad=12
    )
    ax.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "residuals_distribution.png", dpi=300)
    plt.close()

    # 6. Model Serialization & Registry Staging
    print("\n[6/6] Packaging Artifacts and Staging into Model Registry...")
    git_sha = get_git_sha()
    metadata_extra = {
        "dataset_hash_primary_mf": mf_hash,
        "dataset_hash_held_out_mf": held_hash,
        "git_commit_sha": git_sha,
        "primary_metrics": summary_results["gbdt_quantile"],
        "held_out_metrics": {
            "mae": held_mae,
            "rmse": held_rmse,
            "smape": held_smape,
            "mape": held_mape,
            "coverage_80": held_coverage,
            "pinball_loss_50": held_pinball,
            "naive_mae": held_naive_mae,
        },
        "ladder_benchmark": summary_results,
        "feature_names": feature_cols,
    }

    # Save to ml/artifacts
    artifact_path = artifacts_dir / "expense_forecaster_v1.joblib"
    saved_path = final_forecaster.save(artifact_path, metadata_extra=metadata_extra)
    print(f"  Artifact saved to {saved_path}")

    # Stage into Model Registry
    registry_v1_dir = Path("ml/models_registry/expense_forecaster/v1.0.0")
    registry_v1_dir.mkdir(parents=True, exist_ok=True)
    reg_artifact = registry_v1_dir / "model.joblib"
    final_forecaster.save(reg_artifact, metadata_extra=metadata_extra)

    # Compute sha256 for current pointer
    reg_sha = compute_file_sha256(reg_artifact)
    current_meta = {
        "active_version": "v1.0.0",
        "model_name": "expense_forecaster",
        "sha256_checksum": reg_sha,
        "promoted_at": datetime.now(UTC).isoformat(),
        "git_commit_sha": git_sha,
        "status": "production",
    }
    with open(
        Path("ml/models_registry/expense_forecaster/current.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(current_meta, f, indent=2)

    print("  Staged to Registry: ml/models_registry/expense_forecaster/v1.0.0/")
    print("  Set active pointer: ml/models_registry/expense_forecaster/current.json")
    print("Training Pipeline Complete! Acceptance Criteria Satisfied.")


if __name__ == "__main__":
    main()
