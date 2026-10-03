"""Dataset persistence and export engine supporting Parquet, CSV, and sample JSON."""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from data.synthetic.generator.anomalies import AnomalyGroundTruth
from data.synthetic.generator.population import SyntheticUser
from data.synthetic.generator.wallet import SimulationResult


class SyntheticDataWriter:
    """Exports generated synthetic cohorts to Parquet, CSV, and committed JSON samples."""

    def __init__(self, export_dir: Path | None = None) -> None:
        if export_dir is None:
            export_dir = Path("data/exports")
        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def write_dataset(
        self,
        users: list[SyntheticUser],
        sim_results: list[SimulationResult],
        all_anomalies: list[AnomalyGroundTruth],
    ) -> dict[str, int]:
        """Convert objects to DataFrames and export both Parquet and CSV files."""
        # 1. Users DataFrame
        user_rows: list[dict[str, Any]] = []
        user_gt_rows: list[dict[str, Any]] = []
        for u in users:
            user_rows.append(
                {
                    "id": str(u.user_id),
                    "email": u.email,
                    "phone": u.phone,
                    "full_name": u.full_name,
                    "role": "user",
                    "kyc_tier": "tier_1",
                    "is_active": True,
                    "created_at": "2026-01-01T00:00:00+06:00",
                }
            )
            user_gt_rows.append(
                {
                    "id": str(u.user_id),
                    "user_id": str(u.user_id),
                    "true_persona": u.persona,
                    "true_occupation": u.occupation,
                    "baseline_income": float(u.baseline_income),
                    "starting_balance": float(u.starting_balance),
                    "is_drifting": u.is_drifting,
                    "secondary_persona": u.secondary_persona,
                    "drift_month": u.drift_month,
                    "has_festival_bonus": u.has_festival_bonus,
                    "rent_status": u.rent_status,
                    "created_at": "2026-01-01T00:00:00+06:00",
                }
            )

        df_users = pd.DataFrame(user_rows)
        df_user_gt = pd.DataFrame(user_gt_rows)

        # 2. Transactions DataFrame
        txn_rows: list[dict[str, Any]] = []
        contrib_rows: list[dict[str, Any]] = []
        for res in sim_results:
            for t in res.transactions:
                txn_rows.append(
                    {
                        "id": str(t.transaction_id),
                        "user_id": str(t.user_id),
                        "ts": t.ts,
                        "txn_type": t.txn_type,
                        "purpose": t.purpose,
                        "category": t.category,
                        "amount": float(t.amount),
                        "fee": float(t.fee),
                        "balance_after": float(t.balance_after),
                        "idempotency_key": t.idempotency_key,
                        "description": t.description,
                        "merchant_name": t.merchant,
                        "goal_id": str(t.goal_id) if t.goal_id else None,
                    }
                )
            for c in res.goal_contributions:
                contrib_rows.append(
                    {
                        "id": str(c["contribution_id"]),
                        "goal_id": str(c["goal_id"]),
                        "user_id": str(c["user_id"]),
                        "amount": float(str(c["amount"])),
                        "created_at": str(c["created_at"]),
                    }
                )

        df_txns = pd.DataFrame(txn_rows)
        df_contribs = pd.DataFrame(contrib_rows)

        # 3. Financial Goals DataFrame
        goal_rows: list[dict[str, Any]] = []
        for u in users:
            for g in u.goals:
                goal_rows.append(
                    {
                        "id": str(g.goal_id),
                        "user_id": str(u.user_id),
                        "title": g.title,
                        "category": g.category,
                        "target_amount": float(g.target_amount),
                        "current_amount": float(g.current_amount),
                        "target_date": g.target_date.isoformat(),
                        "status": g.status,
                        "created_at": "2026-01-01T00:00:00+06:00",
                    }
                )
        df_goals = pd.DataFrame(goal_rows)

        # 4. Transaction Anomalies Ground Truth DataFrame
        anomaly_rows: list[dict[str, Any]] = []
        for a in all_anomalies:
            anomaly_rows.append(
                {
                    "id": str(a.anomaly_id),
                    "transaction_id": str(a.event_id),
                    "user_id": str(a.user_id),
                    "is_anomaly": True,
                    "anomaly_type": a.anomaly_type,
                    "severity_score": float(a.severity_score),
                    "description": a.description,
                }
            )
        df_anomaly_gt = pd.DataFrame(anomaly_rows)

        # Write Parquet and CSV
        datasets = {
            "users": df_users,
            "synthetic_user_ground_truth": df_user_gt,
            "transactions": df_txns,
            "financial_goals": df_goals,
            "goal_contributions": df_contribs,
            "synthetic_transaction_ground_truth": df_anomaly_gt,
        }

        counts: dict[str, int] = {}
        for name, df in datasets.items():
            parquet_path = self.export_dir / f"{name}.parquet"
            csv_path = self.export_dir / f"{name}.csv"
            df.to_parquet(parquet_path, index=False)
            df.to_csv(csv_path, index=False)
            counts[name] = len(df)

        return counts

    def export_sample(
        self,
        users: list[SyntheticUser],
        sim_results: list[SimulationResult],
        all_anomalies: list[AnomalyGroundTruth],
        sample_dir: Path | None = None,
        count: int = 5,
    ) -> None:
        """Export a committed JSON sample of N full user lifetimes."""
        if sample_dir is None:
            sample_dir = Path("data/synthetic/sample")
        sample_dir.mkdir(parents=True, exist_ok=True)

        sample_users = users[:count]
        sample_user_ids = {u.user_id for u in sample_users}

        # 1. Users Sample
        sample_users_data = [
            {
                "user_id": str(u.user_id),
                "full_name": u.full_name,
                "email": u.email,
                "phone": u.phone,
                "occupation": u.occupation,
                "persona": u.persona,
                "baseline_income": str(u.baseline_income),
                "starting_balance": str(u.starting_balance),
                "rent_status": u.rent_status,
                "is_drifting": u.is_drifting,
                "secondary_persona": u.secondary_persona,
                "drift_month": u.drift_month,
                "has_festival_bonus": u.has_festival_bonus,
            }
            for u in sample_users
        ]
        with open(sample_dir / "users_sample.json", "w", encoding="utf-8") as f:
            json.dump(sample_users_data, f, indent=2)

        # 2. Transactions Sample
        sample_txns_data = []
        for res in sim_results:
            if res.user_id in sample_user_ids:
                for t in res.transactions:
                    sample_txns_data.append(
                        {
                            "transaction_id": str(t.transaction_id),
                            "user_id": str(t.user_id),
                            "ts": t.ts,
                            "txn_type": t.txn_type,
                            "purpose": t.purpose,
                            "category": t.category,
                            "amount": str(t.amount),
                            "fee": str(t.fee),
                            "balance_after": str(t.balance_after),
                            "idempotency_key": t.idempotency_key,
                            "description": t.description,
                            "merchant": t.merchant,
                            "is_anomaly": t.is_anomaly,
                            "anomaly_type": t.anomaly_type,
                        }
                    )
        with open(sample_dir / "transactions_sample.json", "w", encoding="utf-8") as f:
            json.dump(sample_txns_data, f, indent=2)

        # 3. Goals Sample
        sample_goals_data = []
        for u in sample_users:
            for g in u.goals:
                sample_goals_data.append(
                    {
                        "goal_id": str(g.goal_id),
                        "user_id": str(u.user_id),
                        "title": g.title,
                        "category": g.category,
                        "target_amount": str(g.target_amount),
                        "current_amount": str(g.current_amount),
                        "target_date": g.target_date.isoformat(),
                        "status": g.status,
                    }
                )
        with open(sample_dir / "goals_sample.json", "w", encoding="utf-8") as f:
            json.dump(sample_goals_data, f, indent=2)

        # 4. Ground Truth Sample
        sample_gt_data = [
            {
                "anomaly_id": str(a.anomaly_id),
                "transaction_id": str(a.event_id),
                "user_id": str(a.user_id),
                "anomaly_type": a.anomaly_type,
                "severity_score": str(a.severity_score),
                "description": a.description,
            }
            for a in all_anomalies
            if a.user_id in sample_user_ids
        ]
        with open(sample_dir / "ground_truth_sample.json", "w", encoding="utf-8") as f:
            json.dump(sample_gt_data, f, indent=2)
