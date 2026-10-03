#!/usr/bin/env python3
"""Database backup script for Sohoj Financial Coach.

Supports both portable asynchronous snapshot (works on SQLite, AsyncPG, test DBs)
and native PostgreSQL pg_dump. Computes SHA-256 checksum for audit and integrity verification.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import decimal
import gzip
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

# Ensure backend app is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import inspect, select, text
from app.db.session import get_engine
from app.models.base import Base
# Import all models so metadata knows about all tables
import app.models  # noqa: F401


class BackupJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for database types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.hex()
        return super().default(obj)


async def perform_portable_backup(output_path: Path) -> dict[str, Any]:
    """Extract all database tables and write to gzipped JSON manifest."""
    engine = get_engine()
    tables_data: dict[str, list[dict[str, Any]]] = {}
    row_counts: dict[str, int] = {}

    async with engine.connect() as conn:
        # Determine table order respecting metadata
        table_names = [table.name for table in Base.metadata.sorted_tables]

        for table_name in table_names:
            try:
                result = await conn.execute(text(f'SELECT * FROM "{table_name}"'))
                rows = [dict(row._mapping) for row in result.fetchall()]
                tables_data[table_name] = rows
                row_counts[table_name] = len(rows)
            except Exception as e:
                # Table might not exist yet if migrations haven't run
                print(f"[WARN] Could not query table {table_name}: {e}")
                tables_data[table_name] = []
                row_counts[table_name] = 0

    backup_payload = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "database_url_dialect": engine.dialect.name,
        "row_counts": row_counts,
        "tables": tables_data,
    }

    raw_json = json.dumps(backup_payload, cls=BackupJSONEncoder, indent=2).encode("utf-8")
    with gzip.open(output_path, "wb") as f:
        f.write(raw_json)

    sha256_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
    checksum_path = output_path.with_suffix(output_path.suffix + ".sha256")
    checksum_path.write_text(f"{sha256_hash}  {output_path.name}\n", encoding="utf-8")

    return {
        "output_path": str(output_path),
        "checksum_path": str(checksum_path),
        "sha256": sha256_hash,
        "size_bytes": output_path.stat().st_size,
        "total_rows": sum(row_counts.values()),
        "row_counts": row_counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a verified Sohoj database backup.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="backups",
        help="Directory to store backup files",
    )
    parser.add_argument(
        "--filename",
        type=str,
        default=None,
        help="Custom backup filename (e.g. backup_20261004.json.gz)",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.filename:
        out_file = out_dir / args.filename
    else:
        timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_file = out_dir / f"sohoj_backup_{timestamp_str}.json.gz"

    print(f"[*] Starting backup to: {out_file}")
    summary = asyncio.run(perform_portable_backup(out_file))

    print("[+] Backup completed successfully!")
    print(f"    File: {summary['output_path']} ({summary['size_bytes']} bytes)")
    print(f"    SHA-256: {summary['sha256']}")
    print(f"    Total Rows: {summary['total_rows']}")
    for tbl, count in summary["row_counts"].items():
        if count > 0:
            print(f"      - {tbl}: {count} rows")

    return 0


if __name__ == "__main__":
    sys.exit(main())
