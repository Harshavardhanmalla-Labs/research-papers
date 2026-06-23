#!/usr/bin/env python3
"""Live fetch of ExploitDB / public-PoC index.

License-gated. Requires environment variable PAPER1_ENABLE_POC_FETCH=true
to actually contact the network.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from paper1.feeds.poc_client import (
    POC_ENV_FLAG,
    POCClient,
    PoCLicenseGateError,
    normalize_exploitdb_csv,
)
from paper1.utils.logging import get_logger, log_with_context
from paper1.utils.time import parse_date, utc_now


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch ExploitDB / public-PoC index.")
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
    log = get_logger("paper1.scripts.fetch_poc")

    if os.environ.get(POC_ENV_FLAG, "").lower() != "true":
        log_with_context(
            log,
            logging.ERROR,
            "PoC fetch disabled",
            env_flag=POC_ENV_FLAG,
            hint="Set PAPER1_ENABLE_POC_FETCH=true after confirming ExploitDB license terms.",
        )
        return 3

    as_of = parse_date(args.as_of)
    cache_root = Path(args.out)
    manifest_path = Path(args.manifest) if args.manifest else cache_root / "MANIFEST.json"
    client = POCClient(cache_root=cache_root, manifest_path=manifest_path)

    try:
        raw = client.fetch(as_of)
    except PoCLicenseGateError as exc:
        log_with_context(log, logging.ERROR, "license gate refused", error=str(exc))
        return 3

    fetched_at = utc_now()
    df = normalize_exploitdb_csv(raw, as_of, fetched_at=fetched_at)
    path = client.write_snapshot(as_of, df, fetched_at=fetched_at)
    log_with_context(
        log,
        logging.INFO,
        "poc snapshot written",
        path=str(path),
        record_count=len(df),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
