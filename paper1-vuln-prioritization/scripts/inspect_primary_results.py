#!/usr/bin/env python3
"""Inspect, freeze, and compare primary experiment outputs (Phase 14).

Reads primary outputs from disk and reports quality issues before any seeds
are scaled up or any tables are produced. Does not run the pipeline, call
live feeds, or make paper claims.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from paper1.experiments.inspect import (
    compare_primary_runs,
    freeze_primary_results,
    inspect_primary_output,
    verify_freeze_manifest,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Inspect/freeze/compare primary outputs.")
    p.add_argument("--output", default="results/primary_full_v1")
    p.add_argument("--strict", action="store_true", help="Fail (nonzero) on warnings too.")
    p.add_argument("--capacity", type=int, default=None, help="Optional configured capacity.")
    p.add_argument("--freeze", action="store_true", help="Write FREEZE_MANIFEST.json.")
    p.add_argument("--freeze-name", default=None)
    p.add_argument("--overwrite", action="store_true", help="Allow replacing an existing freeze.")
    p.add_argument("--verify-freeze", action="store_true", help="Verify an existing freeze.")
    p.add_argument("--compare-other", default=None, help="Compare against another output dir.")
    return p.parse_args(argv)


def _print_report(report) -> None:
    print("=== primary inspection ===")
    print(f"  output dir:        {report.output_dir}")
    print(f"  seeds:             {report.seed_count}")
    print(f"  strategies:        {report.strategy_count}")
    print(f"  metric rows:       {report.metric_row_count}")
    print(f"  audit logs:        {report.audit_logs_checked} checked, valid={report.audit_logs_valid}")
    print(f"  issue counts:      {report.summary['issue_counts']}")
    print(f"  passed:            {report.passed} (strict={report.summary['strict']})")
    blocking = [i for i in report.issues if i.severity in ("error", "fatal")]
    warnings = [i for i in report.issues if i.severity == "warning"]
    for i in blocking + warnings:
        loc = ":".join(str(x) for x in (i.seed, i.strategy, i.metric) if x is not None)
        print(f"    [{i.severity}] {i.code} {('(' + loc + ') ') if loc else ''}{i.message}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    out = Path(args.output)

    if not out.exists():
        print(
            f"ERROR: output dir not found: {out}\n"
            "  Run a primary run first, e.g.: make primary-one-seed"
        )
        return 2

    exit_code = 0

    report = inspect_primary_output(out, strict=args.strict, capacity=args.capacity)
    _print_report(report)
    if args.strict and not report.passed:
        exit_code = 1

    if args.verify_freeze:
        ok = verify_freeze_manifest(out)
        print(f"  freeze verification: {'OK' if ok else 'FAILED'}")
        if not ok:
            exit_code = 1

    if args.freeze:
        try:
            payload = freeze_primary_results(
                out, freeze_name=args.freeze_name, overwrite=args.overwrite
            )
            print(
                f"  froze {payload['file_count']} files "
                f"({payload['total_bytes']} bytes) -> {out / 'FREEZE_MANIFEST.json'}"
            )
        except FileExistsError as exc:
            print(f"  freeze refused: {exc}")
            exit_code = 1

    if args.compare_other:
        cmp = compare_primary_runs(out, args.compare_other)
        print("=== comparison ===")
        print(f"  seeds A/B:          {cmp['seeds_a']} / {cmp['seeds_b']}")
        print(f"  common seeds:       {cmp['common_seeds']}")
        print(f"  metric rows A/B:    {cmp['metric_row_count_a']} / {cmp['metric_row_count_b']}")
        print(f"  audit valid A/B:    {cmp['audit_valid_a']} / {cmp['audit_valid_b']}")
        print(
            f"  deterministic (common seeds): "
            f"{cmp['deterministic_common_seed_metrics_equal']} "
            f"(diffs={cmp['differences']})"
        )

    if exit_code == 0:
        print("NOTE: Inspection only; not a paper result.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
