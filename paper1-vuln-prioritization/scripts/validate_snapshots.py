#!/usr/bin/env python3
"""Validate the snapshot manifest: every file exists and SHA-256 matches."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from paper1.feeds.provenance import verify_manifest
from paper1.utils.logging import get_logger, log_with_context


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate snapshot manifest checksums.")
    p.add_argument(
        "--manifest",
        default="data/snapshots/MANIFEST.json",
        help="Manifest path (default: data/snapshots/MANIFEST.json)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    log = get_logger("paper1.scripts.validate_snapshots")
    manifest_path = Path(args.manifest)

    ok, issues = verify_manifest(manifest_path)
    if ok:
        log_with_context(log, logging.INFO, "manifest valid", manifest=str(manifest_path))
        return 0
    for issue in issues:
        log_with_context(log, logging.ERROR, "manifest issue", issue=issue)
    log_with_context(
        log,
        logging.ERROR,
        "manifest invalid",
        manifest=str(manifest_path),
        issue_count=len(issues),
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
