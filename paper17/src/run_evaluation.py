#!/usr/bin/env python3
"""Entry point: run the Paper 17 ring-rollout evaluation across seeds 1100 to 1124."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from rollout.model import (  # noqa: E402
    evaluate_seed, EVALUATION_SEEDS, CONFIGS, DETECT_GRID, REF_CONFIG, REF_DETECT,
    FLEET, FAULT_RATE, TRIALS,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path,
                    default=Path(__file__).parent.parent / "results" / "primary_v1")
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for s in EVALUATION_SEEDS:
        rows.extend(evaluate_seed(s))
    df = pd.DataFrame(rows)
    df.to_csv(args.output_dir / "primary_results.csv", index=False)
    print(f"Wrote {len(df)} rows -> primary_results.csv")

    manifest = {
        "evaluation_seeds": EVALUATION_SEEDS, "configs": CONFIGS, "detect_grid": DETECT_GRID,
        "ref_config": REF_CONFIG, "ref_detect": REF_DETECT, "fleet": FLEET,
        "fault_rate": FAULT_RATE, "monte_carlo_trials": TRIALS, "n_rows": int(len(df)),
    }
    with open(args.output_dir / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print("\n=== Expected blast radius by config (p_detect=0.80) ===")
    cfg = df[df.axis == "config"].groupby("config")["expected_blast"].mean()
    for name in ["big-bang", "2-ring", "4-ring", "6-ring"]:
        print(f"  {name:10s} {cfg[name]:.4f}")


if __name__ == "__main__":
    main()
