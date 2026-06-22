#!/usr/bin/env python3
"""Entry point: run the Paper 18 resilience evaluation across seeds 1200 to 1224."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from resilience.model import (  # noqa: E402
    evaluate_seed, EVALUATION_SEEDS, N_MODES, N_FRAGILE, FRAGILE_RATE, ROBUST_RATE,
    HORIZON_DAYS, REF_CHAOS_CADENCE, REF_COVERAGE, COVERAGE_GRID, CADENCE_GRID,
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
        "evaluation_seeds": EVALUATION_SEEDS, "n_modes": N_MODES, "n_fragile": N_FRAGILE,
        "fragile_rate": FRAGILE_RATE, "robust_rate": ROBUST_RATE, "horizon_days": HORIZON_DAYS,
        "ref_chaos_cadence": REF_CHAOS_CADENCE, "ref_coverage": REF_COVERAGE,
        "coverage_grid": COVERAGE_GRID, "cadence_grid": CADENCE_GRID, "n_rows": int(len(df)),
    }
    with open(args.output_dir / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    ref = df[df.axis == "reference"]
    print(f"\nReference: annual recovery {ref['rec_random_annual'].mean():.3f} -> "
          f"chaos {ref['rec_random_chaos'].mean():.3f} (gain {ref['gain'].mean():.3f})")
    di = df[df.axis == "drill_interval"]
    print("Drill illusion by interval:",
          {int(i): round(di[di.interval == i]['illusion'].mean(), 3) for i in [365, 180, 90, 30]})


if __name__ == "__main__":
    main()
