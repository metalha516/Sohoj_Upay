"""High-performance database bulk loader for synthetic financial datasets."""

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Ensure backend/ is on sys.path
_root_dir = Path(__file__).resolve().parents[2]
_backend_dir = _root_dir / "backend"
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.core.config import get_settings  # noqa: E402


@dataclass
class LoadResult:
    connected: bool
    tables_loaded: dict[str, int]
    sql_script_path: Path | None
    message: str


class SyntheticDataLoader:
    """Loads Parquet/CSV synthetic datasets into PostgreSQL schema or generates bulk SQL."""

    def __init__(self, data_dir: Path | None = None) -> None:
        if data_dir is None:
            data_dir = Path("data/exports")
        self.data_dir = data_dir
        self.settings = get_settings()

    def generate_bulk_copy_sql(self, output_path: Path | None = None) -> Path:
        """Generate a production-ready SQL script for psql / COPY execution."""
        if output_path is None:
            output_path = self.data_dir / "bulk_load.sql"

        sql_statements = [
            "-- =============================================================================",
            "-- Sohoj Synthetic Data Bulk Loader Script",
            "-- Target Engine: PostgreSQL 16 + pgvector",
            "-- =============================================================================",
            "BEGIN;",
            "SET LOCAL statement_timeout = 0;",
            "SET LOCAL synchronous_commit = OFF;",
            "",
        ]

        # Order of tables honoring foreign key dependencies:
        # 1. users
        # 2. synthetic_user_ground_truth
        # 3. financial_goals
        # 4. transactions
        # 5. goal_contributions
        # 6. synthetic_transaction_ground_truth
        tables = [
            "users",
            "synthetic_user_ground_truth",
            "financial_goals",
            "transactions",
            "goal_contributions",
            "synthetic_transaction_ground_truth",
        ]

        for table in tables:
            csv_file = self.data_dir / f"{table}.csv"
            if csv_file.exists():
                abs_csv = csv_file.resolve().as_posix()
                sql_statements.append(f"-- Bulk load {table}")
                sql_statements.append(
                    f"\\copy {table} FROM '{abs_csv}' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');"
                )
                sql_statements.append("")

        sql_statements.append("COMMIT;")
        sql_statements.append("-- Bulk load completed successfully.")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sql_statements))

        return output_path

    async def load_into_database(self) -> LoadResult:
        """Attempt live bulk loading into PostgreSQL via asyncpg if reachable."""
        try:
            import asyncpg
        except ImportError:
            sql_path = self.generate_bulk_copy_sql()
            return LoadResult(
                connected=False,
                tables_loaded={},
                sql_script_path=sql_path,
                message="asyncpg not installed; generated bulk_load.sql for manual execution.",
            )

        db_url = self.settings.database_url
        # Convert postgresql+asyncpg:// or postgresql:// to postgresql://
        raw_dsn = str(db_url).replace("postgresql+asyncpg://", "postgresql://")

        try:
            conn = await asyncio.wait_for(asyncpg.connect(raw_dsn), timeout=3.0)
        except Exception as e:
            sql_path = self.generate_bulk_copy_sql()
            return LoadResult(
                connected=False,
                tables_loaded={},
                sql_script_path=sql_path,
                message=f"PostgreSQL unreachable ({e}). Generated offline bulk COPY script: {sql_path}",
            )

        tables_loaded: dict[str, int] = {}
        tables = [
            "users",
            "synthetic_user_ground_truth",
            "financial_goals",
            "transactions",
            "goal_contributions",
            "synthetic_transaction_ground_truth",
        ]

        try:
            async with conn.transaction():
                for table in tables:
                    parquet_file = self.data_dir / f"{table}.parquet"
                    if parquet_file.exists():
                        df = pd.read_parquet(parquet_file)
                        records = [tuple(row) for row in df.itertuples(index=False)]
                        cols = list(df.columns)
                        col_names = ", ".join(cols)
                        val_placeholders = ", ".join(f"${i + 1}" for i in range(len(cols)))
                        stmt = f"INSERT INTO {table} ({col_names}) VALUES ({val_placeholders}) ON CONFLICT DO NOTHING"
                        await conn.executemany(stmt, records)
                        count = await conn.fetchval(f"SELECT count(*) FROM {table}")
                        tables_loaded[table] = int(count)
        finally:
            await conn.close()

        sql_path = self.generate_bulk_copy_sql()
        return LoadResult(
            connected=True,
            tables_loaded=tables_loaded,
            sql_script_path=sql_path,
            message="Successfully loaded all synthetic datasets into live PostgreSQL database.",
        )
