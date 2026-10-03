import argparse
import sys
from pathlib import Path

import pandas as pd

# Ensure backend/ and root are on sys.path
_root_dir = Path(__file__).resolve().parents[2]
_backend_dir = _root_dir / "backend"
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from data.synthetic.generator.engine import SyntheticDataOrchestrator  # noqa: E402
from data.synthetic.generator.writer import SyntheticDataWriter  # noqa: E402


def cmd_generate(args: argparse.Namespace) -> int:
    """Execute synthetic dataset generation, export Parquet/CSV, and dump JSON samples."""
    print(f"[*] Starting synthetic data generation: users={args.users}, seed={args.seed}")
    config_dir = Path(args.config_dir)
    export_dir = Path(args.export_dir)
    sample_dir = Path(args.sample_dir)

    orchestrator = SyntheticDataOrchestrator(config_dir=config_dir, seed=args.seed)
    users, sim_results, all_anomalies, report = orchestrator.generate(num_users=args.users)

    print(f"[+] Simulation completed in {report.elapsed_seconds:.2f}s!")
    print(f"    - Total Users: {report.total_users}")
    print(f"    - Total Transactions: {report.total_transactions:,}")
    print(f"    - Total Goals: {report.total_goals:,}")
    print(f"    - Total Contributions: {report.total_contributions:,}")
    print(f"    - Total Anomalies: {report.total_anomalies:,} ({report.anomaly_rate * 100:.2f}%)")
    print(f"    - Wallet Invariant Failures: {report.invariant_failures}")

    if report.invariant_failures > 0:
        print("[!] ERROR: Wallet invariants failed for one or more users!", file=sys.stderr)
        return 1

    # Write full dataset
    writer = SyntheticDataWriter(export_dir=export_dir)
    counts = writer.write_dataset(users, sim_results, all_anomalies)
    print(f"[+] Exported Parquet and CSV files to: {export_dir}")
    for name, cnt in counts.items():
        print(f"    - {name}: {cnt:,} rows")

    # Export committed sample
    writer.export_sample(
        users, sim_results, all_anomalies, sample_dir=sample_dir, count=args.sample_count
    )
    print(f"[+] Exported {args.sample_count}-user sample JSON to: {sample_dir}")

    # Print breakdown tables
    print("\n--- Breakdown by Persona ---")
    for p, c in sorted(report.persona_counts.items(), key=lambda x: -x[1]):
        print(f"  {p:25s}: {c:4d} ({c / report.total_users * 100:5.1f}%)")

    print("\n--- Breakdown by Occupation ---")
    for o, c in sorted(report.occupation_counts.items(), key=lambda x: -x[1]):
        print(f"  {o:25s}: {c:4d} ({c / report.total_users * 100:5.1f}%)")

    print("\n--- Breakdown by Transaction Type ---")
    for t, c in sorted(report.type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t:25s}: {c:6d} ({c / report.total_transactions * 100:5.1f}%)")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate generated dataset integrity, balances, and non-negativity."""
    data_dir = Path(args.data_dir)
    print(f"[*] Validating synthetic dataset in: {data_dir}")

    txns_path = data_dir / "transactions.parquet"
    if not txns_path.exists():
        print(f"[!] File not found: {txns_path}", file=sys.stderr)
        return 1

    df_txns = pd.read_parquet(txns_path)
    print(f"[+] Loaded {len(df_txns):,} transactions across {df_txns['user_id'].nunique()} users")

    # 1. Non-negative balances check
    neg_balances = (df_txns["balance_after"] < 0).sum()
    if neg_balances > 0:
        print(
            f"[!] FAILED: Found {neg_balances} transactions with negative balance_after!",
            file=sys.stderr,
        )
        return 1
    print("[PASS] 100% of transaction balance_after values are non-negative.")

    # 2. Positive amounts check
    non_pos_amounts = (df_txns["amount"] <= 0).sum()
    if non_pos_amounts > 0:
        print(
            f"[!] FAILED: Found {non_pos_amounts} transactions with non-positive amounts!",
            file=sys.stderr,
        )
        return 1
    print("[PASS] 100% of transaction amount values are strictly positive.")

    # 3. Purpose required check for expense and cash_out
    missing_purpose = (
        df_txns[df_txns["txn_type"].isin(["expense", "cash_out"])]["purpose"].isna().sum()
    )
    if missing_purpose > 0:
        print(
            f"[!] FAILED: Found {missing_purpose} expenses/cash-outs missing purpose!",
            file=sys.stderr,
        )
        return 1
    print("[PASS] 100% of expense and cash_out transactions have purpose defined.")

    print("\n[ALL CHECKS PASSED] Dataset validation successful!")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic Financial Data Generator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: generate
    p_gen = subparsers.add_parser("generate", help="Generate synthetic population and transactions")
    p_gen.add_argument(
        "--users", type=int, default=600, help="Number of users to simulate (default: 600)"
    )
    p_gen.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation (default: 42)",
    )
    p_gen.add_argument(
        "--config-dir", type=str, default="data/synthetic/config", help="Config directory"
    )
    p_gen.add_argument(
        "--export-dir", type=str, default="data/exports", help="Export directory for Parquet/CSV"
    )
    p_gen.add_argument(
        "--sample-dir", type=str, default="data/synthetic/sample", help="Sample directory for JSON"
    )
    p_gen.add_argument(
        "--sample-count", type=int, default=5, help="Number of sample users to export (default: 5)"
    )

    # Subcommand: validate
    p_val = subparsers.add_parser("validate", help="Validate dataset invariants and non-negativity")
    p_val.add_argument("--data-dir", type=str, default="data/exports", help="Dataset directory")

    # Subcommand: load
    p_load = subparsers.add_parser(
        "load", help="Bulk-load synthetic dataset into PostgreSQL database"
    )
    p_load.add_argument("--data-dir", type=str, default="data/exports", help="Dataset directory")

    args = parser.parse_args()
    if args.command == "generate":
        sys.exit(cmd_generate(args))
    elif args.command == "validate":
        sys.exit(cmd_validate(args))
    elif args.command == "load":
        sys.exit(cmd_load(args))


def cmd_load(args: argparse.Namespace) -> int:
    """Execute database bulk loading or emission of bulk COPY SQL script."""
    import asyncio

    from data.synthetic.loader import SyntheticDataLoader

    data_dir = Path(args.data_dir)
    print(f"[*] Starting bulk load for datasets in: {data_dir}")
    loader = SyntheticDataLoader(data_dir=data_dir)
    res = asyncio.run(loader.load_into_database())
    print(f"[{'PASS' if res.connected else 'INFO'}] {res.message}")
    if res.tables_loaded:
        for t, cnt in res.tables_loaded.items():
            print(f"    - {t}: {cnt:,} rows in PostgreSQL")
    elif res.sql_script_path:
        print(f"[+] Bulk SQL script ready: {res.sql_script_path}")
    return 0


if __name__ == "__main__":
    main()
