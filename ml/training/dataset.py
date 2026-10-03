"""Dataset assembler and feature extractor for Model A (Behavior Classification).

Extracts scale-invariant, dimensionless ratio features from monthly_features
and aligns them with user-level ground-truth behavioral persona targets.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

FEATURE_NAMES = [
    "savings_rate",
    "necessity_rate",
    "discretionary_rate",
    "income_expense_ratio",
    "cashout_frequency",
    "rolling_sr_mean",
    "rolling_sr_std",
    "savings_consistency",
    "category_entropy",
    "discretionary_volatility",
    "deficit_months",
    "spending_growth",
    "expense_cv",
    "spending_trend_pct",
]

TARGET_PROFILES = [
    "balanced_spender",
    "cash_dominant_transactor",
    "consistent_saver",
    "discretionary_spender",
    "tight_budgeter",
    "volatile_earner",
]


def compute_file_sha256(path: Path | str) -> str:
    """Compute SHA-256 hex digest of a file for dataset provenance and integrity."""
    p = Path(path)
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def extract_features_from_dict(row: dict[str, Any]) -> np.ndarray:
    """Extract the 14-dimensional dimensionless feature vector from a single monthly feature dict."""
    txn_count = float(row.get("txn_count") or 1.0)
    cashout_count = float(row.get("cashout_count") or 0.0)
    cashout_freq = cashout_count / max(txn_count, 1.0)

    avg_txn = float(row.get("avg_txn") or 1.0)
    exp_var = float(row.get("expense_variance") or 0.0)
    exp_cv = float(np.sqrt(max(0.0, exp_var)) / max(avg_txn, 1.0))

    rolling_exp = float(row.get("rolling_expense_3m_mean") or 1.0)
    trend_3m = float(row.get("spending_trend_3m") or 0.0)
    trend_pct = trend_3m / max(rolling_exp, 1.0)

    vec = [
        float(row.get("savings_rate") or 0.0),
        float(row.get("necessity_rate") or 0.0),
        float(row.get("discretionary_rate") or 0.0),
        float(row.get("income_expense_ratio") or 1.0),
        cashout_freq,
        float(row.get("rolling_savings_rate_3m_mean") or 0.0),
        float(row.get("rolling_savings_rate_3m_std") or 0.0),
        float(row.get("savings_consistency") or 0.0),
        float(row.get("category_entropy_3m") or 0.0),
        float(row.get("discretionary_volatility_3m") or 0.0),
        float(row.get("deficit_months_3m") or 0.0),
        float(row.get("spending_growth") or 0.0),
        exp_cv,
        trend_pct,
    ]
    return np.asarray(vec, dtype=np.float64)


def prepare_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare clean, scale-invariant feature DataFrame from monthly_features DataFrame."""
    res = pd.DataFrame(index=df.index)

    # 1. Savings rate
    res["savings_rate"] = df["savings_rate"].fillna(0.0).astype(float)

    # 2. Expense composition
    res["necessity_rate"] = df["necessity_rate"].fillna(0.0).astype(float)
    res["discretionary_rate"] = df["discretionary_rate"].fillna(0.0).astype(float)
    res["income_expense_ratio"] = df["income_expense_ratio"].fillna(1.0).astype(float)

    # 3. Cash-out liquidity reliance
    txn_count = np.maximum(df["txn_count"].fillna(1.0).astype(float), 1.0)
    res["cashout_frequency"] = (df["cashout_count"].fillna(0.0).astype(float) / txn_count).astype(
        float
    )

    # 4. Rolling savings metrics
    res["rolling_sr_mean"] = df["rolling_savings_rate_3m_mean"].fillna(0.0).astype(float)
    res["rolling_sr_std"] = df["rolling_savings_rate_3m_std"].fillna(0.0).astype(float)
    res["savings_consistency"] = df["savings_consistency"].fillna(0.0).astype(float)

    # 5. Category entropy & volatility
    res["category_entropy"] = df["category_entropy_3m"].fillna(0.0).astype(float)
    res["discretionary_volatility"] = df["discretionary_volatility_3m"].fillna(0.0).astype(float)
    res["deficit_months"] = df["deficit_months_3m"].fillna(0.0).astype(float)
    res["spending_growth"] = df["spending_growth"].fillna(0.0).astype(float)

    # 6. Coefficient of variation (dimensionless variance)
    avg_txn = np.maximum(df["avg_txn"].fillna(1.0).astype(float), 1.0)
    exp_std = np.sqrt(np.maximum(df["expense_variance"].fillna(0.0).astype(float), 0.0))
    res["expense_cv"] = (exp_std / avg_txn).astype(float)

    # 7. Normalized spending trend
    rolling_exp = np.maximum(df["rolling_expense_3m_mean"].fillna(1.0).astype(float), 1.0)
    res["spending_trend_pct"] = (
        df["spending_trend_3m"].fillna(0.0).astype(float) / rolling_exp
    ).astype(float)

    return res[FEATURE_NAMES]


def load_dataset(
    data_dir: Path | str,
    exclude_drifting: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, pd.DataFrame, str]:
    """Load monthly features and ground-truth persona labels for model training/evaluation.

    Returns:
        X: (N, 14) feature matrix
        y: (N,) string label array
        groups: (N,) user_id array for GroupKFold
        df_merged: full merged dataframe with metadata
        dataset_hash: SHA-256 hash of the monthly features parquet file
    """
    d = Path(data_dir)
    feat_path = d / "monthly_features.parquet"
    truth_path = d / "synthetic_user_ground_truth.parquet"

    if not feat_path.exists():
        raise FileNotFoundError(f"Monthly features file not found: {feat_path}")
    if not truth_path.exists():
        raise FileNotFoundError(f"User ground truth file not found: {truth_path}")

    dataset_hash = compute_file_sha256(feat_path)

    df_feat = pd.read_parquet(feat_path)
    df_truth = pd.read_parquet(truth_path)

    # Merge on user_id
    df_merged = df_feat.merge(
        df_truth[["user_id", "true_persona", "is_drifting", "secondary_persona"]],
        on="user_id",
        how="inner",
    )

    if exclude_drifting:
        df_merged = df_merged[df_merged["true_persona"] != "mixed_drifting"].copy()

    df_X = prepare_feature_matrix(df_merged)

    X = np.asarray(df_X.values, dtype=np.float64)
    y = np.asarray(df_merged["true_persona"].tolist(), dtype=str)
    groups = np.asarray(df_merged["user_id"].astype(str).tolist(), dtype=str)

    return X, y, groups, df_merged, dataset_hash
