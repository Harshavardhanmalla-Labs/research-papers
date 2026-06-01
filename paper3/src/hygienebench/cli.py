"""
CLI entry points for HygieneBench.

  python -m hygienebench.cli generate --seed 42 --condition c_base --scale medium --output datasets/
  python -m hygienebench.cli validate datasets/c_base_seed42_medium/
"""

from __future__ import annotations
import argparse
import json
import os
import sys


def main_generate() -> None:
    parser = argparse.ArgumentParser(description="Generate a HygieneBench synthetic dataset.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--condition", choices=["c_base", "c_fresh", "c_stale", "c_miss", "c_unsup"],
                        default="c_base")
    parser.add_argument("--scale", choices=["small", "medium", "large"], default="medium")
    parser.add_argument("--tasks", default="all",
                        help="Comma-separated task IDs (T1,T2,...) or 'all'")
    parser.add_argument("--output", default="datasets/")
    args = parser.parse_args()

    from hygienebench.config import GeneratorConfig, ConditionConfig
    from hygienebench.generator import SyntheticHygieneGenerator
    from hygienebench.injector import AnomalyInjector
    from hygienebench.splitter import assign_splits
    from hygienebench.cards import save_dataset_card

    cond_map = {
        "c_base": ConditionConfig.c_base,
        "c_fresh": ConditionConfig.c_fresh,
        "c_stale": ConditionConfig.c_stale,
        "c_miss": ConditionConfig.c_miss,
        "c_unsup": ConditionConfig.c_unsup,
    }
    scale_map = {
        "small": GeneratorConfig.small,
        "medium": GeneratorConfig.medium,
        "large": GeneratorConfig.large,
    }

    condition = cond_map[args.condition]()
    config = scale_map[args.scale](seed=args.seed, condition=condition)

    if args.tasks == "all":
        tasks = ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]
    else:
        tasks = [t.strip().upper() for t in args.tasks.split(",")]
    config.tasks = tasks

    print(f"Generating: seed={args.seed} condition={args.condition} scale={args.scale} tasks={tasks}")

    gen = SyntheticHygieneGenerator(config)
    ds = gen.generate()

    injector = AnomalyInjector(seed=args.seed)
    ds = injector.inject(ds, tasks=tasks)

    ds = assign_splits(ds)

    out_dir = os.path.join(args.output, ds.dataset_id)
    ds.save(out_dir)
    save_dataset_card(ds, out_dir)

    summary = ds.summary()
    splits_info = ds.anomaly_labels["split"].value_counts().to_dict() if len(ds.anomaly_labels) > 0 else {}

    print(f"Saved to: {out_dir}")
    print(f"  users: {summary['n_users']} | computers: {summary['n_computers']} "
          f"| login_events: {summary['n_login_events']} | vuln_records: {summary['n_vulnerability_records']}")
    print(f"  anomaly_labels: {summary['n_anomaly_labels']} | splits: {splits_info}")
    print(f"  anomaly_class_counts: {summary['anomaly_class_counts']}")


def main_validate() -> None:
    parser = argparse.ArgumentParser(description="Validate a HygieneBench dataset directory.")
    parser.add_argument("dataset_dir")
    args = parser.parse_args()

    from hygienebench.validate import validate_dataset
    passed, report = validate_dataset(args.dataset_dir)
    print(json.dumps(report, indent=2))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    sub = sys.argv[1] if len(sys.argv) > 1 else "generate"
    if sub == "generate":
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        main_generate()
    elif sub == "validate":
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        main_validate()
    else:
        print(f"Unknown subcommand: {sub}. Use 'generate' or 'validate'.")
        sys.exit(1)
