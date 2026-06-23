#!/usr/bin/env python3
"""Entry point: run the Paper 12 compliance-exposure evaluation across seeds 800 to 824."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from compliance.model import (  # noqa: E402
    evaluate_seed, EVALUATION_SEEDS, N_CONTROLS, HORIZON_DAYS, MTTR_DAYS,
    FRAC_HIGH_DRIFT, HIGH_DRIFT_RATE, LOW_DRIFT_RATE, AUTO_PROB_HIGH, AUTO_PROB_LOW,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path,
                    default=Path(__file__).parent.parent / "results" / "primary_v1")
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows = [evaluate_seed(s) for s in EVALUATION_SEEDS]
    df = pd.DataFrame(rows)
    df.to_csv(args.output_dir / "primary_results.csv", index=False)
    print(f"Wrote {len(df)} rows -> primary_results.csv")

    manifest = {
        "evaluation_seeds": EVALUATION_SEEDS, "n_controls": N_CONTROLS,
        "horizon_days": HORIZON_DAYS, "mttr_days": MTTR_DAYS,
        "frac_high_drift": FRAC_HIGH_DRIFT, "high_drift_rate": HIGH_DRIFT_RATE,
        "low_drift_rate": LOW_DRIFT_RATE, "auto_prob_high": AUTO_PROB_HIGH,
        "auto_prob_low": AUTO_PROB_LOW, "cadences": {"annual": 365, "quarterly": 90, "continuous": 1},
        "n_rows": int(len(df)),
    }
    with open(args.output_dir / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print("\n=== Means across seeds ===")
    for c in ["automatable_fraction", "mttd_auto_ratio", "reduction_vs_annual",
              "automatable_exposure_share", "ceiling_gap", "top_quartile_capture"]:
        print(f"  {c:30s} {df[c].mean():.4f}")


if __name__ == "__main__":
    main()
