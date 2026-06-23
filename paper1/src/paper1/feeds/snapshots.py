"""Snapshot file IO.

Each snapshot is a single self-describing JSON file containing the
source name, the as-of date, fetch timestamp, source version, schema
version, and the normalized records. Snapshot writes are atomic.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from paper1.utils.io import atomic_write_json, read_json
from paper1.utils.time import ensure_utc, parse_date

__all__ = [
    "SNAPSHOT_SCHEMA_VERSION",
    "load_snapshot",
    "snapshot_path",
    "write_snapshot",
]

SNAPSHOT_SCHEMA_VERSION = "1"


def snapshot_path(cache_root: str | Path, source_name: str, as_of_date: date) -> Path:
    """Deterministic on-disk path for a snapshot file."""
    if not isinstance(as_of_date, date) or isinstance(as_of_date, datetime):
        raise TypeError("as_of_date must be a date (not datetime)")
    if not source_name or "/" in source_name:
        raise ValueError(f"Invalid source_name: {source_name!r}")
    yyyymmdd = as_of_date.strftime("%Y%m%d")
    return Path(cache_root) / source_name / f"{source_name}_{yyyymmdd}.json"


def write_snapshot(
    cache_root: str | Path,
    source_name: str,
    as_of_date: date,
    df: pd.DataFrame,
    *,
    fetched_at: datetime,
    source_version: str | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Atomically write a normalized snapshot to disk.

    Returns the absolute path written. The on-disk JSON layout is:

        {
          "source_name": "...",
          "as_of_date": "YYYY-MM-DD",
          "fetched_at": "...UTC...",
          "source_version": "..." | null,
          "schema_version": "1",
          "record_count": N,
          "extra": {...},
          "records": [{...}, ...]
        }
    """
    ensure_utc(fetched_at)
    target = snapshot_path(cache_root, source_name, as_of_date)

    # Ensure deterministic record ordering for hash stability.
    if not df.empty and "cve_id" in df.columns:
        df = df.sort_values("cve_id", kind="mergesort").reset_index(drop=True)

    records = df.to_dict(orient="records")
    payload = {
        "source_name": source_name,
        "as_of_date": as_of_date.isoformat(),
        "fetched_at": fetched_at.isoformat().replace("+00:00", "Z"),
        "source_version": source_version,
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "record_count": len(records),
        "extra": extra or {},
        "records": records,
    }
    atomic_write_json(target, payload)
    return target


def load_snapshot(path: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load a snapshot file; return (records_dataframe, metadata)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Snapshot not found: {p}")
    payload = read_json(p)
    required_meta = {
        "source_name",
        "as_of_date",
        "fetched_at",
        "schema_version",
        "record_count",
        "records",
    }
    missing = required_meta - set(payload.keys())
    if missing:
        raise ValueError(f"Snapshot {p} missing required keys: {sorted(missing)}")
    if payload["schema_version"] != SNAPSHOT_SCHEMA_VERSION:
        raise ValueError(
            f"Snapshot {p} schema_version {payload['schema_version']!r} "
            f"does not match expected {SNAPSHOT_SCHEMA_VERSION!r}"
        )
    records = payload["records"]
    if len(records) != payload["record_count"]:
        raise ValueError(
            f"Snapshot {p} record_count mismatch: "
            f"declared {payload['record_count']}, actual {len(records)}"
        )
    df = pd.DataFrame.from_records(records) if records else pd.DataFrame()
    meta = {k: v for k, v in payload.items() if k != "records"}
    # Normalize as_of_date back to date.
    meta["as_of_date"] = parse_date(meta["as_of_date"])
    return df, meta
