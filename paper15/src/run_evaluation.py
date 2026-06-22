#!/usr/bin/env python3
"""Entry point: run the Paper 15 telemetry-fusion evaluation across seeds 1000 to 1024."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from fusion.model import (  # noqa: E402
    evaluate_seed, EVALUATION_SEEDS, OVERLAP_GRID, REF_OVERLAP,
    N_ASSETS, COV_REALTIME, COV_SCHEDULED, SCHED_FRESH, VULN_PREVALENCE,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path,
                    default=Path(__file__).parent.parent / "results" / "primary_v1")
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for s in EVALUATION_SEEDS:
        rows.extend(r for r in evaluate_seed(s) if r)
    df = pd.DataFrame(rows)
    df.to_csv(args.output_dir / "primary_results.csv", index=False)
    print(f"Wrote {len(df)} rows -> primary_results.csv")

    manifest = {
        "evaluation_seeds": EVALUATION_SEEDS, "overlap_grid": OVERLAP_GRID,
        "ref_overlap": REF_OVERLAP, "n_assets": N_ASSETS,
        "cov_realtime": COV_REALTIME, "cov_scheduled": COV_SCHEDULED,
        "scheduled_fresh": SCHED_FRESH, "vuln_prevalence": VULN_PREVALENCE,
        "n_rows": int(len(df)),
    }
    with open(args.output_dir / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print("\n=== Means at reference overlap ===")
    ref = df[df.overlap == REF_OVERLAP]
    for c in ["recall_realtime", "recall_scheduled", "recall_fusion",
              "gain_over_best_single", "blind_spot"]:
        print(f"  {c:24s} {ref[c].mean():.4f}")


if __name__ == "__main__":
    main()
