"""Unit tests for dataset realism validator, statistical gate, and bulk loader."""

from pathlib import Path

import pandas as pd
import pytest
from data.synthetic.loader import SyntheticDataLoader
from ml.preprocessing.validate_dataset import DatasetRealismValidator


def test_bulk_loader_generates_sql(tmp_path: Path) -> None:
    """Verify SyntheticDataLoader generates valid bulk copy SQL in FK dependency order."""
    tables = [
        "users",
        "synthetic_user_ground_truth",
        "financial_goals",
        "transactions",
        "goal_contributions",
        "synthetic_transaction_ground_truth",
    ]
    for t in tables:
        (tmp_path / f"{t}.csv").touch()

    loader = SyntheticDataLoader(data_dir=tmp_path)
    sql_path = tmp_path / "bulk_load.sql"
    generated_path = loader.generate_bulk_copy_sql(output_path=sql_path)

    assert generated_path.exists()
    content = generated_path.read_text(encoding="utf-8")
    assert "\\copy users" in content
    assert "\\copy transactions" in content
    assert "\\copy financial_goals" in content
    assert "\\copy goal_contributions" in content
    assert "\\copy synthetic_user_ground_truth" in content
    assert "\\copy synthetic_transaction_ground_truth" in content

    # Assert users comes before transactions (FK dependency)
    user_idx = content.index("\\copy users")
    txn_idx = content.index("\\copy transactions")
    assert user_idx < txn_idx


def test_realism_validator_full_suite(tmp_path: Path) -> None:
    """Verify that all 10 realism checks pass on the generated primary cohort."""
    data_dir = Path("data/exports")
    if not (data_dir / "transactions.parquet").exists():
        pytest.skip("data/exports not yet generated")

    validator = DatasetRealismValidator(data_dir=data_dir, figures_dir=tmp_path / "figures")
    results = validator.run_all_checks()
    assert len(results) == 10
    for r in results:
        assert r.passed is True, f"Realism check {r.check_id} failed: {r.summary}"


def test_leakage_isolation_detector(tmp_path: Path) -> None:
    """Verify that any leaked ground-truth column in transactions or users triggers failure."""
    # Create minimal mock datasets
    users = pd.DataFrame(
        {
            "id": ["u1"],
            "email": ["u1@example.test"],
            "phone_number": ["+8801700000001"],
            "full_name": ["User One"],
            "is_active": [True],
            "created_at": ["2026-01-01T00:00:00Z"],
        }
    )
    user_gt = pd.DataFrame(
        {
            "user_id": ["u1"],
            "true_persona": ["balanced_spender"],
            "true_occupation": ["student"],
            "baseline_income": [15000.0],
            "is_drifting": [False],
            "secondary_persona": [None],
            "drift_month": [None],
        }
    )
    txns = pd.DataFrame(
        {
            "id": ["t1"],
            "user_id": ["u1"],
            "ts": ["2026-01-01T12:00:00+06:00"],
            "txn_type": ["expense"],
            "category": ["groceries"],
            "purpose": ["necessity"],
            "amount": [500.0],
            "fee": [0.0],
            "balance_after": [14500.0],
        }
    )
    goals = pd.DataFrame({"id": [], "user_id": []})
    contribs = pd.DataFrame({"id": [], "goal_id": []})
    txn_gt = pd.DataFrame({"transaction_id": [], "user_id": [], "is_anomaly": []})

    users.to_parquet(tmp_path / "users.parquet")
    user_gt.to_parquet(tmp_path / "synthetic_user_ground_truth.parquet")
    txns.to_parquet(tmp_path / "transactions.parquet")
    goals.to_parquet(tmp_path / "financial_goals.parquet")
    contribs.to_parquet(tmp_path / "goal_contributions.parquet")
    txn_gt.to_parquet(tmp_path / "synthetic_transaction_ground_truth.parquet")

    validator = DatasetRealismValidator(data_dir=tmp_path, figures_dir=tmp_path / "figures")

    # Clean state should pass leakage check
    leakage_result = validator.check_leakage_isolation()
    assert leakage_result.passed is True
    assert len(leakage_result.metrics["txn_leaks"]) == 0
    assert len(leakage_result.metrics["user_leaks"]) == 0

    # Infiltrate a forbidden ground-truth column into transactions
    validator.df_txns["true_persona"] = "balanced_spender"
    polluted_result = validator.check_leakage_isolation()
    assert polluted_result.passed is False
    assert "true_persona" in polluted_result.metrics["txn_leaks"]
