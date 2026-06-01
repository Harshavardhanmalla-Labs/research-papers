#!/usr/bin/env python3
"""Run the end-to-end smoke experiment (Phase 11).

Pipeline verification only -- toy fixtures, deterministic seeds, no live
feeds, no paper results. See configs/experiment_smoke.yaml.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from paper1.experiments.smoke import _DEFAULT_CONFIG, _load_smoke_config, run_smoke_experiment
from paper1.utils.config import load_yaml


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the end-to-end smoke experiment.")
    p.add_argument(
        "--config",
        default=str(_DEFAULT_CONFIG),
        help="Path to the experiment config (default: configs/experiment_smoke.yaml)",
    )
    p.add_argument(
        "--out",
        default=None,
        help="Optional output_dir override (defaults to the config's output_dir)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    config_path = args.config

    if args.out is not None:
        # Materialize an override config next to the requested output dir so
        # the manifest's config_sha still reflects the exact bytes used.
        import yaml  # local import; only needed for the override path

        cfg = _load_smoke_config(config_path)
        cfg = dict(cfg)
        cfg["output_dir"] = args.out
        out_root = Path(args.out)
        out_root.mkdir(parents=True, exist_ok=True)
        override_path = out_root / "experiment_smoke.resolved.yaml"
        override_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        config_path = str(override_path)
    else:
        # Touch the config to fail fast with a clear error if missing.
        load_yaml(config_path)

    summary = run_smoke_experiment(config_path)

    print("=== smoke experiment summary ===")
    print(f"  output dir:        {summary['output_dir']}")
    print(f"  seeds:             {summary['seeds']}")
    print(f"  pair count range:  {summary['pair_count_min']} .. {summary['pair_count_max']}")
    print(f"  strategies ({summary['strategy_count']}):  {summary['strategies']}")
    print(f"  audit logs valid:  {summary['audit_logs_valid']}")
    print(f"  metric rows:       {summary['metric_rows']}")
    print("NOTE: Smoke verification only; not a paper result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
