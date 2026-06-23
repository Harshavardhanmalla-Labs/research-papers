#!/usr/bin/env python3
"""Live fetch of daily FIRST EPSS snapshots over a date window.

Resumable: if a snapshot for a date already exists and its file
SHA-256 matches the manifest entry, the date is skipped.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

from paper1.feeds.epss_client import EPSS_HISTORY_BEGIN, EPSSClient, normalize_epss_csv
from paper1.feeds.provenance import (
    load_manifest,
    snapshot_id,
    verify_snapshot_file,
)
from paper1.utils.io import compute_file_sha256
from paper1.utils.logging import get_logger, log_with_context
from paper1.utils.time import parse_date, utc_now


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch daily EPSS snapshots into cache.")
    p.add_argument("--start", required=True, help="Window start date YYYY-MM-DD")
    p.add_argument("--end", required=True, help="Window end date YYYY-MM-DD")
    p.add_argument("--out", default="data/snapshots", help="Snapshot cache root")
    p.add_argument(
        "--manifest",
        default=None,
        help="Manifest path (default: <out>/MANIFEST.json)",
    )
    return p.parse_args(argv)


def _already_cached(
    client: EPSSClient, as_of: date, manifest: dict
) -> bool:
    path = client.snapshot_path(as_of)
    if not path.exists():
        return False
    sid = snapshot_id(client.source_name, as_of)
    for entry in manifest.get("snapshots", []):
        if snapshot_id(entry["source_name"], parse_date(entry["snapshot_date"])) != sid:
            continue
        return verify_snapshot_file(path, entry["sha256"])
    # No manifest entry but file present — re-register from existing file.
    return False


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    log = get_logger("paper1.scripts.fetch_epss")

    start = parse_date(args.start)
    end = parse_date(args.end)
    if end < start:
        log_with_context(log, logging.ERROR, "end < start", start=str(start), end=str(end))
        return 2
    if start < EPSS_HISTORY_BEGIN:
        log_with_context(
            log,
            logging.ERROR,
            "start before EPSS history begin",
            start=str(start),
            begin=str(EPSS_HISTORY_BEGIN),
        )
        return 2

    cache_root = Path(args.out)
    manifest_path = Path(args.manifest) if args.manifest else cache_root / "MANIFEST.json"
    client = EPSSClient(cache_root=cache_root, manifest_path=manifest_path)

    cur = start
    fetched_count = 0
    skipped_count = 0
    while cur <= end:
        manifest = load_manifest(manifest_path)
        if _already_cached(client, cur, manifest):
            skipped_count += 1
            log_with_context(log, logging.INFO, "epss skip cached", date=str(cur))
        else:
            raw_bytes = client.fetch(cur)
            df = normalize_epss_csv(raw_bytes, cur, fetched_at=utc_now())
            path = client.write_snapshot(cur, df, fetched_at=utc_now())
            fetched_count += 1
            log_with_context(
                log,
                logging.INFO,
                "epss snapshot written",
                date=str(cur),
                path=str(path),
                record_count=len(df),
                sha=compute_file_sha256(path),
            )
        cur += timedelta(days=1)

    log_with_context(
        log,
        logging.INFO,
        "fetch_epss done",
        fetched=fetched_count,
        skipped=skipped_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
