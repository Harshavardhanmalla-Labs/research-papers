#!/usr/bin/env python3
"""
Entry point: run the full HygienePrio evaluation.

Usage:
    python src/run_evaluation.py --output-dir results/primary_results_v1/

This script runs all 9 methods across 25 evaluation seeds, computing
P@K, NDCG@K, and Oracle-gap at K=50, 100, 250.

All results are bounded to the synthetic EEHDA fleet evaluation context.
See paper4/manuscript/paper4_draft_v0.1.md §9 for threats to validity.
"""

import argparse
import sys
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).parent))

from hygieneprio.evaluate import run_evaluation, EVALUATION_SEEDS


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run HygienePrio evaluation across all seeds."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "results" / "primary_results_v1",
        help="Directory to write primary_results.csv and run_manifest.json.",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=None,
        help="Override evaluation seeds (default: pre-registered 25 seeds).",
    )
    args = parser.parse_args()

    seeds = args.seeds or EVALUATION_SEEDS
    print(f"HygienePrio evaluation: {len(seeds)} seeds → {args.output_dir}")

    df = run_evaluation(seeds=seeds, output_dir=args.output_dir)

    # Quick summary
    print("\n=== P@50 Summary (mean across seeds) ===")
    summary = (
        df.groupby("method")["p_at_50"]
        .agg(["mean", "std"])
        .sort_values("mean", ascending=False)
    )
    print(summary.round(3).to_string())
    print("\nDone. All results are from a synthetic EEHDA fleet (not real enterprise data).")


if __name__ == "__main__":
    main()
