#!/usr/bin/env python3
"""Entry point: run the Paper 19 CMDB-reconciliation evaluation across seeds 1300 to 1324."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from cmdb.model import (  # noqa: E402
    evaluate_seed, EVALUATION_SEEDS, MEAN_LIFETIME, QUIET_FRACTION, OBS_NORMAL, OBS_QUIET,
    PERIODIC_CADENCE, CONTINUOUS_CADENCE, REF_RETIRE, REF_PRECISION, RETIRE_GRID, PRECISION_GRID,
    N_ASSETS,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path,
                    default=Path(__file__).parent.parent / "results" / "primary_v1")
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for s in EVALUATION_SEEDS:
        print(f"  seed {s}...", end=" ", flush=True)
        rows.extend(evaluate_seed(s))
        print("done")
    df = pd.DataFrame(rows)
    df.to_csv(args.output_dir / "primary_results.csv", index=False)
    print(f"Wrote {len(df)} rows -> primary_results.csv")

    manifest = {
        "evaluation_seeds": EVALUATION_SEEDS, "mean_lifetime": MEAN_LIFETIME,
        "quiet_fraction": QUIET_FRACTION, "obs_normal": OBS_NORMAL, "obs_quiet": OBS_QUIET,
        "periodic_cadence": PERIODIC_CADENCE, "continuous_cadence": CONTINUOUS_CADENCE,
        "ref_retire": REF_RETIRE, "ref_precision": REF_PRECISION,
        "retire_grid": RETIRE_GRID, "precision_grid": PRECISION_GRID,
        "monte_carlo_assets": N_ASSETS, "n_rows": int(len(df)),
    }
    with open(args.output_dir / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    reg = df[df.axis == "regime"]
    for name in ["continuous", "periodic"]:
        r = reg[reg.regime == name]
        print(f"  {name:11s} ghost {r['ghost_rate'].mean():.4f}  phantom {r['phantom_rate'].mean():.4f}"
              f"  total {r['total_error'].mean():.4f}")


if __name__ == "__main__":
    main()
