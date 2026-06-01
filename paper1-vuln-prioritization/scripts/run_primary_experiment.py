#!/usr/bin/env python3
"""Run the primary experiment runner (Phase 13: controlled execution).

Safety model:
  - dry-run configs run the guardrailed dry-run;
  - a non-dry-run config runs ONLY with --confirm-full-run AND an explicit
    --max-seeds (it never defaults to all seeds);
  - --max-seeds > 3 requires --allow-large-run;
  - --plan validates + estimates and executes nothing.

No live feeds. Output is NOT a final paper result unless all pre-registered
seeds complete and outputs are frozen.
"""

from __future__ import annotations

import argparse
import json
import sys

from paper1.experiments.primary import (
    _DEFAULT_CONFIG,
    load_primary_config,
    plan_primary_run,
    run_primary_confirmed,
    run_primary_dryrun,
)

_DISCLAIMER = (
    "This is controlled primary execution, not a final paper result unless all "
    "pre-registered seeds complete and outputs are frozen."
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the primary experiment (controlled).")
    p.add_argument("--config", default=str(_DEFAULT_CONFIG))
    p.add_argument("--dry-run", action="store_true", help="Force a dry-run.")
    p.add_argument("--plan", action="store_true", help="Validate + estimate only; run nothing.")
    p.add_argument(
        "--max-seeds",
        type=int,
        default=None,
        help="Seeds to run (REQUIRED for a confirmed non-dry run).",
    )
    p.add_argument(
        "--confirm-full-run",
        action="store_true",
        help="Required to execute a non-dry-run config.",
    )
    p.add_argument(
        "--allow-large-run",
        action="store_true",
        help="Required when --max-seeds > 3.",
    )
    p.add_argument("--out", default=None, help="Optional output_dir override.")
    return p.parse_args(argv)


def _print_plan(plan: dict) -> None:
    print("=== primary RUN PLAN (nothing executed) ===")
    print(f"  config name:        {plan['config_name']}")
    print(f"  dry_run:            {plan['dry_run']}")
    print(f"  fleet_size:         {plan['fleet_size']} (capacity/window {plan['capacity']})")
    print(f"  seeds requested:    {plan['seeds_requested']}")
    print(f"  seeds would run:    {plan['seeds_would_run']}")
    print(f"  strategy count:     {plan['strategy_count']}")
    print(f"  output dir:         {plan['output_dir']}")
    print(f"  guardrails:         {json.dumps(plan['guardrails'])}")
    est = plan["estimate"]
    print("  estimate:           " + json.dumps({k: est[k] for k in est if k != "warnings"}))
    for w in est["warnings"]:
        print(f"    [warn] {w}")


def _print_dry(summary: dict) -> None:
    print("=== primary DRY-RUN summary ===")
    print(f"  config name:        {summary['config_name']}")
    print(f"  fleet_size:         {summary['fleet_size']} (capacity/window {summary['capacity']})")
    print(f"  seeds run:          {summary['seeds']}")
    print(f"  strategies:         {summary['strategy_count']}")
    print(f"  output dir:         {summary['output_dir']}")
    print(f"  audit logs valid:   {summary['audit_logs_valid']}")
    print(f"  metric rows:        {summary['metric_rows']}")
    print("NOTE: Dry-run infrastructure only; not a paper result.")


def _print_confirmed(summary: dict) -> None:
    print("=== primary CONTROLLED-RUN summary ===")
    print(f"  config name:        {summary['config_name']}")
    print(f"  fleet_size:         {summary['fleet_size']} (capacity/window {summary['capacity']})")
    print(f"  seeds requested:    {summary['seeds_requested']}")
    print(f"  seeds run:          {summary['seeds_run']}")
    print(f"  seeds skipped:      {summary['seeds_skipped_from_checkpoint']} (resumed)")
    print(f"  strategies:         {summary['strategy_count']}")
    print(f"  output dir:         {summary['output_dir']}")
    print(f"  audit logs valid:   {summary['audit_logs_valid']}")
    print(f"  metric rows:        {summary['metric_rows']}")
    print(f"  runtime seconds:    {summary['runtime_seconds']:.2f}")
    print(f"NOTE: {summary['note']}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    config = load_primary_config(args.config)
    print(_DISCLAIMER)

    # Plan mode: validate + estimate, execute nothing.
    if args.plan:
        _print_plan(plan_primary_run(args.config, max_seeds=args.max_seeds))
        return 0

    # Dry-run config (or forced dry-run).
    if config.dry_run or args.dry_run:
        summary = run_primary_dryrun(
            args.config, max_seeds=args.max_seeds or 1, out_override=args.out
        )
        _print_dry(summary)
        return 0

    # Non-dry-run config: controlled execution, heavily guarded.
    if not args.confirm_full_run:
        print(
            "REFUSING: non-dry-run config requires --confirm-full-run.\n"
            "  Start with: --plan, then --confirm-full-run --max-seeds 1."
        )
        return 2
    if args.max_seeds is None:
        print(
            "REFUSING: a confirmed non-dry-run requires an explicit --max-seeds "
            "(it never defaults to all seeds). Try --max-seeds 1 first."
        )
        return 2
    if args.max_seeds > 3 and not args.allow_large_run:
        print(
            f"REFUSING: --max-seeds {args.max_seeds} (>3) requires --allow-large-run."
        )
        return 2

    summary = run_primary_confirmed(
        config,
        max_seeds=args.max_seeds,
        out_override=args.out,
        allow_large_run=args.allow_large_run,
    )
    _print_confirmed(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
