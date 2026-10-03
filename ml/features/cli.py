"""CLI tool for feature store backfill and incremental recomputation."""

import argparse
import json
import sys
import time
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd

from ml.features.engine import MonthlyFeatureEngine

FORBIDDEN_LEAKAGE_COLUMNS = {
    "true_persona",
    "true_occupation",
    "is_anomaly",
    "anomaly_type",
    "severity_score",
    "is_drifting",
    "secondary_persona",
}


def cmd_backfill(args: argparse.Namespace) -> int:
    """Execute full feature store backfill across all cohort users."""
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Starting full feature backfill from: {data_dir}")
    start_time = time.time()

    txn_file = data_dir / "transactions.parquet"
    if not txn_file.exists():
        print(f"[!] Error: Transactions file not found at {txn_file}", file=sys.stderr)
        return 1

    df_txns = pd.read_parquet(txn_file)
    print(
        f"    - Loaded {len(df_txns):,} transactions across {df_txns['user_id'].nunique()} users."
    )

    engine = MonthlyFeatureEngine()
    all_feature_records: list[dict[str, Any]] = []

    # Group by user_id
    user_groups = df_txns.groupby("user_id")
    total_users = len(user_groups)

    for i, (user_id_val, user_df) in enumerate(user_groups, start=1):
        u_uuid = uuid.UUID(str(user_id_val))
        records = engine.compute_user_features(u_uuid, user_df)
        for r in records:
            d = r.model_dump()
            # Serialize Decimal and Date for DataFrame storage
            d["user_id"] = str(d["user_id"])
            d["month"] = d["month"].isoformat()
            d["category_breakdown"] = json.dumps(d["category_breakdown"])
            d["computed_at"] = d["computed_at"].isoformat()
            # Cast Decimals to float for parquet export
            for k, v in d.items():
                if isinstance(v, Decimal):
                    d[k] = float(v)
            all_feature_records.append(d)

        if i % 100 == 0 or i == total_users:
            print(
                f"    - Processed {i}/{total_users} users ({len(all_feature_records):,} monthly records)..."
            )

    elapsed = time.time() - start_time
    print(f"[+] Feature computation completed in {elapsed:.2f} seconds!")

    # Build DataFrame
    df_features = pd.DataFrame(all_feature_records)

    # -------------------------------------------------------------------------
    # Anti-Leakage Audit
    # -------------------------------------------------------------------------
    leaks = FORBIDDEN_LEAKAGE_COLUMNS.intersection(set(df_features.columns))
    if leaks:
        print(
            f"[!] ERROR: Ground-truth leakage detected in feature table: {leaks}!", file=sys.stderr
        )
        return 1
    print("[+] Anti-leakage audit PASSED: 0 forbidden ground-truth columns present.")

    # -------------------------------------------------------------------------
    # Null Rates Documentation
    # -------------------------------------------------------------------------
    print("\n--- Feature Null Rates Audit ---")
    null_rates = (df_features.isnull().mean() * 100.0).round(2)
    for col, rate in null_rates.items():
        print(f"  {col:32s}: {rate:5.2f}% null")

    # Export Parquet & CSV
    parquet_path = output_dir / "monthly_features.parquet"
    csv_path = output_dir / "monthly_features.csv"

    df_features.to_parquet(parquet_path, index=False)
    df_features.to_csv(csv_path, index=False)

    print("\n[+] Exported features:")
    print(f"    - Parquet: {parquet_path} ({len(df_features):,} rows)")
    print(f"    - CSV:     {csv_path}")

    return 0


def cmd_recompute(args: argparse.Namespace) -> int:
    """Execute incremental recomputation for a single (user_id, month)."""
    data_dir = Path(args.data_dir)
    user_id = uuid.UUID(args.user_id)
    target_month = date.fromisoformat(args.month)

    print(f"[*] Incremental recompute for user={user_id}, month={target_month}")
    df_txns = pd.read_parquet(data_dir / "transactions.parquet")
    user_txns = df_txns[df_txns["user_id"] == str(user_id)]

    engine = MonthlyFeatureEngine()
    updated = engine.recompute_user_month_features(user_id, target_month, user_txns)

    print(f"[+] Recomputed {len(updated)} affected month(s):")
    for r in updated:
        print(f"\nMonth {r.month} Feature Snapshot:")
        print(f"  - Income:               BDT {r.income}")
        print(f"  - Expense:              BDT {r.expense}")
        print(f"  - Savings:              BDT {r.savings}")
        print(f"  - Savings Rate:         {r.savings_rate}")
        print(f"  - Necessity Rate:       {r.necessity_rate}")
        print(f"  - Cash-Out Count:       {r.cashout_count}")
        print(f"  - 3M Rolling SR Mean:   {r.rolling_savings_rate_3m_mean}")
        print(f"  - 3M Category Entropy:  {r.category_entropy_3m}")
        print(f"  - Deficit Months (3M):  {r.deficit_months_3m}")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Feature Engineering Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # backfill
    p_backfill = subparsers.add_parser("backfill", help="Run full cohort feature backfill")
    p_backfill.add_argument("--data-dir", type=str, default="data/exports", help="Input directory")
    p_backfill.add_argument(
        "--output-dir", type=str, default="data/exports", help="Output directory"
    )

    # recompute
    p_recompute = subparsers.add_parser("recompute", help="Incremental recompute for (user, month)")
    p_recompute.add_argument("--user-id", type=str, required=True, help="User UUID")
    p_recompute.add_argument("--month", type=str, required=True, help="Month ISO YYYY-MM-01")
    p_recompute.add_argument("--data-dir", type=str, default="data/exports", help="Input directory")

    args = parser.parse_args()

    if args.command == "backfill":
        sys.exit(cmd_backfill(args))
    elif args.command == "recompute":
        sys.exit(cmd_recompute(args))


if __name__ == "__main__":
    main()
