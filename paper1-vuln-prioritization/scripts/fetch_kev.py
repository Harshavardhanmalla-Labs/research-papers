#!/usr/bin/env python3
"""Live fetch of the CISA KEV catalog (reconstructed as-of snapshot)."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from paper1.feeds.kev_client import KEVClient
from paper1.utils.logging import get_logger, log_with_context
from paper1.utils.time import parse_date, utc_now


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch CISA KEV catalog as-of snapshot.")
    p.add_argument("--as-of", required=True, help="As-of date YYYY-MM-DD")
    p.add_argument("--out", default="data/snapshots", help="Snapshot cache root")
    p.add_argument(
        "--manifest",
        default=None,
        help="Manifest path (default: <out>/MANIFEST.json)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    log = get_logger("paper1.scripts.fetch_kev")
    as_of = parse_date(args.as_of)
    cache_root = Path(args.out)
    manifest_path = Path(args.manifest) if args.manifest else cache_root / "MANIFEST.json"

    client = KEVClient(cache_root=cache_root, manifest_path=manifest_path)
    raw = client.fetch(as_of)
    fetched_at = utc_now()
    df = client.normalize(raw, as_of)
    path = client.write_snapshot(
        as_of,
        df,
        fetched_at=fetched_at,
        extra={"reconstructed_asof_from_current_catalog": True},
    )
    log_with_context(
        log,
        logging.INFO,
        "kev snapshot written",
        path=str(path),
        record_count=len(df),
        as_of=str(as_of),
        skipped=df.attrs.get("skipped_count", 0),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
