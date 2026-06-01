"""
run_evaluation.py — top-level script for all HygieneBench primary evaluations.

Usage:
  PYTHONPATH=src .venv/bin/python src/run_evaluation.py \
    --conditions c_base c_stale c_fresh c_miss c_unsup \
    --seeds 42 137 2024 \
    --results-dir results/primary_full_v1

Runs all 840 planned evaluations:
  5 conditions × 7 tasks × 8 methods × 3 seeds
  (M8 excluded from T4, T5 → 5×5×8×3 + 5×2×7×3 = 600 + 210 = 810 actual runs)
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

# Allow running as: PYTHONPATH=src python src/run_evaluation.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from hygienebench.evaluation.runner import EvaluationRunner
from hygienebench.evaluation.methods import ALL_METHOD_IDS


DATASETS_ROOT = os.path.join(os.path.dirname(__file__), "..", "datasets")

# Dataset directory naming convention used by the generator CLI
CONDITION_DIR_PATTERN = {
    "c_base":  "hygienebench_v0.1_c_base_seed{seed}_n1000",
    "c_fresh": "hygienebench_v0.1_c_fresh_seed{seed}_n1000",
    "c_stale": "hygienebench_v0.1_c_stale_seed{seed}_n1000",
    "c_miss":  "hygienebench_v0.1_c_miss_seed{seed}_n1000",
    "c_unsup": "hygienebench_v0.1_c_unsup_seed{seed}_n1000",
}


def _resolve_dataset_dir(condition_id: str, seed: int, datasets_root: str) -> str | None:
    """Return the dataset directory for a given condition and seed, or None if not found."""
    pattern = CONDITION_DIR_PATTERN.get(condition_id, "")
    if not pattern:
        return None
    name = pattern.format(seed=seed)
    path = os.path.join(datasets_root, name)
    if os.path.isdir(path):
        return path
    # Fallback: glob search
    matches = glob.glob(os.path.join(datasets_root, f"*{condition_id}*seed{seed}*"))
    return matches[0] if matches else None


def build_dataset_dirs(
    conditions: list[str],
    seeds: list[int],
    datasets_root: str,
) -> dict[str, str]:
    """
    Build {condition_id: dataset_dir} mapping.

    For multi-seed setups, EvaluationRunner is called once per condition and
    iterates over seeds itself. We pick the first available seed's directory
    as the canonical dataset_dir, since the runner re-extracts features per
    seed using the seed parameter in TaskFeatureExtractor.extract(task_id, seed).

    Note: each dataset_dir is a condition×seed snapshot. The runner uses the
    dataset_dir for the matching seed.
    """
    # Build {condition_id_seed: path} then hand to runner as extended condition keys
    result = {}
    for cond in conditions:
        for seed in seeds:
            key = f"{cond}_seed{seed}"
            d = _resolve_dataset_dir(cond, seed, datasets_root)
            if d is not None:
                result[key] = d
            else:
                print(f"[WARN] Dataset not found for {cond} seed={seed}, skipping.")
    return result


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run HygieneBench evaluation suite")
    p.add_argument(
        "--conditions", nargs="+",
        default=["c_base", "c_stale", "c_fresh", "c_miss", "c_unsup"],
        help="Condition IDs to evaluate",
    )
    p.add_argument(
        "--seeds", nargs="+", type=int,
        default=[42, 137, 2024],
        help="Random seeds",
    )
    p.add_argument(
        "--tasks", nargs="+",
        default=["T1", "T2", "T3", "T4", "T5", "T6", "T7"],
        help="Task IDs to evaluate",
    )
    p.add_argument(
        "--methods", nargs="+",
        default=list(ALL_METHOD_IDS),
        help="Method IDs to evaluate",
    )
    p.add_argument(
        "--datasets-root", default=DATASETS_ROOT,
        help="Root directory containing dataset subdirectories",
    )
    p.add_argument(
        "--results-dir", default="results/primary_full_v1",
        help="Directory to write result CSVs and manifests",
    )
    p.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-run progress output",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    print("HygieneBench Evaluation Suite v0.1")
    print(f"  Conditions : {args.conditions}")
    print(f"  Seeds      : {args.seeds}")
    print(f"  Tasks      : {args.tasks}")
    print(f"  Methods    : {args.methods}")
    print(f"  Datasets   : {args.datasets_root}")
    print(f"  Results    : {args.results_dir}")
    print()

    dataset_dirs = build_dataset_dirs(args.conditions, args.seeds, args.datasets_root)

    if not dataset_dirs:
        print("ERROR: No dataset directories resolved. Run generate first.")
        sys.exit(1)

    print(f"Resolved {len(dataset_dirs)} dataset directories:")
    for k, v in dataset_dirs.items():
        print(f"  {k}: {v}")
    print()

    runner = EvaluationRunner(
        dataset_dirs=dataset_dirs,
        seeds=args.seeds,
        tasks=args.tasks,
        methods=args.methods,
        results_dir=args.results_dir,
        verbose=not args.quiet,
    )

    df = runner.run()

    total = len(df)
    errors = int((df["error"] != "").sum()) if not df.empty else 0
    print(f"\nDone. {total} runs, {errors} errors, {total - errors} successful.")

    manifest_path = os.path.join(args.results_dir, "run_manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
        neg_rate = manifest.get("negative_result_rate")
        flagged = manifest.get("failure_flagged_configs", 0)
        total_cfg = manifest.get("total_method_task_condition_configs", 0)
        print(f"Failure flags: {flagged}/{total_cfg} configs ({neg_rate:.1%} negative-result rate)")


if __name__ == "__main__":
    main()
