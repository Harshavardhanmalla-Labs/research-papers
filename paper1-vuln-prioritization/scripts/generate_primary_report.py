#!/usr/bin/env python3
"""Generate paper-ready tables and figures from the FROZEN primary artifact.

Reads only the frozen primary outputs (after verifying the freeze manifest).
Produces no interpretation and no paper claims; interpretation belongs in
Phase 18.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from paper1.experiments.inspect import verify_freeze_manifest
from paper1.reporting.report_bundle import generate_primary_report_bundle


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate primary report from frozen outputs.")
    p.add_argument("--output", default="results/primary_full_v1")
    p.add_argument("--report-dir", default=None, help="Default: <output>/report")
    p.add_argument("--paper-dir", default="paper")
    p.add_argument("--capacity", type=int, default=100)
    p.add_argument(
        "--verify-freeze",
        action="store_true",
        help="Verify the freeze before generating (also done implicitly by the loader).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    out = Path(args.output)

    if not out.exists():
        print(f"ERROR: output dir not found: {out}\n  Run the primary experiment first.")
        return 2

    # Default behaviour verifies the freeze (the loader re-verifies regardless).
    verified = verify_freeze_manifest(out)
    print(f"freeze verification: {'OK' if verified else 'FAILED'}")
    if not verified:
        print("REFUSING: cannot generate a report from an unverified/missing freeze.")
        return 1

    report_dir = args.report_dir or str(out / "report")
    manifest = generate_primary_report_bundle(
        out, report_dir=report_dir, paper_dir=args.paper_dir, capacity=args.capacity
    )

    print(f"source artifact:   {manifest['source_output_dir']}")
    print(f"tables generated:  {len(manifest['table_files'])}")
    for name in sorted(manifest["table_files"]):
        print(f"    - {name} (csv/md/tex)")
    print(f"figures generated: {len(manifest['figure_files'])}")
    for name in sorted(manifest["figure_files"]):
        print(f"    - {name} (png/pdf)")
    print(f"report manifest:   {Path(report_dir) / 'report_manifest.json'}")
    print(f"paper dir:         {args.paper_dir}")
    if manifest["warnings"]:
        print("warnings:")
        for w in manifest["warnings"]:
            print(f"    [warn] {w}")
    print(
        "NOTE: Tables/figures are generated from frozen primary outputs; "
        "interpretation belongs in Phase 18."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
