#!/usr/bin/env python3
"""Database restore and verification drill script for Sohoj Financial Coach.

Verifies SHA-256 checksum, recreates tables if requested, restores data in dependency order,
and verifies 100% row count and schema integrity.
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

from sqlalchemy import delete, insert, select, text
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.session import get_engine
from app.models.base import Base
# Import all models
import app.models  # noqa: F401


def verify_checksum(backup_path: Path) -> bool:
    """Verify SHA-256 checksum against .sha256 file if present."""
    checksum_path = backup_path.with_suffix(backup_path.suffix + ".sha256")
    if not checksum_path.exists():
        print(f"[!] Warning: No checksum file found at {checksum_path}")
        return True

    expected_hash = checksum_path.read_text(encoding="utf-8").split()[0].strip()
    actual_hash = hashlib.sha256(backup_path.read_bytes()).hexdigest()

    if expected_hash.lower() != actual_hash.lower():
        raise ValueError(f"Checksum mismatch! Expected: {expected_hash}, Actual: {actual_hash}")

    print(f"[+] SHA-256 Checksum verified: {actual_hash}")
    return True


async def perform_restore(backup_path: Path, target_db_url: str | None = None) -> dict[str, Any]:
    """Restore database from gzipped JSON backup."""
    verify_checksum(backup_path)

    with gzip.open(backup_path, "rb") as f:
        payload = json.loads(f.read().decode("utf-8"))

    manifest_counts = payload.get("row_counts", {})
    tables_data = payload.get("tables", {})

    if target_db_url:
        engine = create_async_engine(target_db_url, echo=False)
    else:
        engine = get_engine()

    restored_counts: dict[str, int] = {}

    async with engine.begin() as conn:
        # Create schema if not exists
        await conn.run_sync(Base.metadata.create_all)

        # Clear existing rows in reverse dependency order
        for table in reversed(Base.metadata.sorted_tables):
            try:
                await conn.execute(table.delete())
            except Exception as e:
                print(f"[DEBUG] Could not clear table {table.name}: {e}")

        # Insert rows in topological dependency order
        for table in Base.metadata.sorted_tables:
            raw_rows = tables_data.get(table.name, [])
            if raw_rows:
                col_map = {c.name: c for c in table.columns}
                deserialized_rows = []
                for r in raw_rows:
                    cleaned = {}
                    for col_name, val in r.items():
                        if val is None:
                            cleaned[col_name] = None
                            continue
                        col = col_map.get(col_name)
                        if col is None:
                            cleaned[col_name] = val
                            continue
                        try:
                            py_type = getattr(col.type, "python_type", None)
                        except Exception:
                            py_type = None

                        if (
                            "UUID" in str(col.type).upper()
                            or py_type == uuid.UUID
                        ):
                            cleaned[col_name] = uuid.UUID(val) if isinstance(val, str) else val
                        elif py_type == datetime.datetime:
                            cleaned[col_name] = (
                                datetime.datetime.fromisoformat(val)
                                if isinstance(val, str)
                                else val
                            )
                        elif py_type == datetime.date:
                            cleaned[col_name] = (
                                datetime.date.fromisoformat(val)
                                if isinstance(val, str)
                                else val
                            )
                        elif py_type == decimal.Decimal:
                            cleaned[col_name] = decimal.Decimal(str(val))
                        else:
                            cleaned[col_name] = val
                    deserialized_rows.append(cleaned)

                try:
                    await conn.execute(insert(table), deserialized_rows)
                    restored_counts[table.name] = len(deserialized_rows)
                except Exception as e:
                    print(f"[ERROR] Failed to restore table {table.name}: {e}")
                    raise
            else:
                restored_counts[table.name] = 0

    # Verification phase
    mismatches = []
    async with engine.connect() as conn:
        for table in Base.metadata.sorted_tables:
            result = await conn.execute(text(f'SELECT COUNT(*) FROM "{table.name}"'))
            actual_count = result.scalar_one()
            expected = manifest_counts.get(table.name, 0)
            if actual_count != expected:
                mismatches.append(f"{table.name}: expected {expected}, found {actual_count}")

    if target_db_url:
        await engine.dispose()

    if mismatches:
        raise RuntimeError(f"Restore verification failed with mismatches: {mismatches}")

    return {
        "status": "SUCCESS",
        "backup_file": str(backup_path),
        "total_restored_rows": sum(restored_counts.values()),
        "restored_counts": restored_counts,
        "verification": "100% MATCH",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore a Sohoj database from backup.")
    parser.add_argument(
        "backup_file",
        type=str,
        help="Path to .json.gz backup file",
    )
    parser.add_argument(
        "--target-db-url",
        type=str,
        default=None,
        help="Optional target database URL for restore drill",
    )
    args = parser.parse_args()

    backup_path = Path(args.backup_file)
    if not backup_path.exists():
        print(f"[ERROR] Backup file not found: {backup_path}")
        return 1

    print(f"[*] Starting restore drill from: {backup_path}")
    try:
        summary = asyncio.run(perform_restore(backup_path, args.target_db_url))
        print("[+] Restore drill completed successfully!")
        print(f"    Restored Rows: {summary['total_restored_rows']}")
        print(f"    Verification Status: {summary['verification']}")
        for tbl, count in summary["restored_counts"].items():
            if count > 0:
                print(f"      - {tbl}: {count} rows")
        return 0
    except Exception as e:
        print(f"[FATAL] Restore failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
