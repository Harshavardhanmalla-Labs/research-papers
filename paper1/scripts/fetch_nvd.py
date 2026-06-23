#!/usr/bin/env python3
"""Live fetch of the NVD CVE 2.0 API for a publication-date window.

Not invoked during unit tests. Writes one snapshot per as-of-date
(taken to be the window's end date) and registers it in the manifest.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from paper1.feeds.nvd_client import NVDClient, fetch_nvd_window
from paper1.utils.logging import get_logger, log_with_context
from paper1.utils.time import parse_date, utc_now


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch NVD CVEs into snapshot cache.")
    p.add_argument("--start", required=True, help="Window start date YYYY-MM-DD")
    p.add_argument("--end", required=True, help="Window end date YYYY-MM-DD")
    p.add_argument(
        "--out",
        default="data/snapshots",
        help="Snapshot cache root (default: data/snapshots)",
    )
    p.add_argument(
        "--api-key-env",
        default="NVD_API_KEY",
        help="Environment variable holding an NVD API key (optional)",
    )
    p.add_argument(
        "--manifest",
        default=None,
        help="Manifest path (default: <out>/MANIFEST.json)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    log = get_logger("paper1.scripts.fetch_nvd")

    start = parse_date(args.start)
    end = parse_date(args.end)
    if end < start:
        log_with_context(log, logging.ERROR, "end < start", start=str(start), end=str(end))
        return 2

    api_key = os.environ.get(args.api_key_env) if args.api_key_env else None
    cache_root = Path(args.out)
    manifest_path = Path(args.manifest) if args.manifest else cache_root / "MANIFEST.json"

    log_with_context(
        log,
        logging.INFO,
        "fetch_nvd start",
        start=str(start),
        end=str(end),
        cache_root=str(cache_root),
        api_key=bool(api_key),
    )

    raw = fetch_nvd_window(start, end, api_key=api_key)
    log_with_context(log, logging.INFO, "fetch_nvd raw count", count=len(raw))

    client = NVDClient(cache_root=cache_root, manifest_path=manifest_path)
    df = client.normalize({"vulnerabilities": raw}, end)
    fetched_at = utc_now()
    path = client.write_snapshot(end, df, fetched_at=fetched_at)

    log_with_context(
        log,
        logging.INFO,
        "fetch_nvd snapshot written",
        path=str(path),
        record_count=len(df),
        warnings=len(df.attrs.get("normalization_warnings", [])),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
