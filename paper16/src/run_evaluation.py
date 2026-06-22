#!/usr/bin/env python3
"""Entry point: run the Paper 16 hygiene-anomaly evaluation across seeds 700 to 724."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from hygieneml.model import (  # noqa: E402
    evaluate_seed, EVALUATION_SEEDS, DETECTORS, CONDITIONS,
    N_HOSTS, ANOMALY_PREV, SDA_SHIFT, WITHIN_CHANNEL_CORR, N_FEATURES,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path,
                    default=Path(__file__).parent.parent / "results" / "primary_v1")
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for seed in EVALUATION_SEEDS:
        print(f"  seed {seed}...", end=" ", flush=True)
        rows.extend(evaluate_seed(seed))
        print("done")
    df = pd.DataFrame(rows)
    df.to_csv(args.output_dir / "primary_results.csv", index=False)
    print(f"Wrote {len(df)} rows -> primary_results.csv")

    manifest = {
        "evaluation_seeds": EVALUATION_SEEDS, "detectors": DETECTORS, "conditions": CONDITIONS,
        "n_hosts": N_HOSTS, "anomaly_prevalence": ANOMALY_PREV, "sda_shift": SDA_SHIFT,
        "within_channel_corr": WITHIN_CHANNEL_CORR, "n_features": N_FEATURES,
        "detector_settings": {"IsolationForest": "200 trees", "OneClassSVM": "rbf, nu=0.1",
                              "LocalOutlierFactor": "20 neighbors"},
        "n_rows": int(len(df)),
    }
    with open(args.output_dir / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print("\n=== Mean average precision by condition x detector ===")
    piv = df.groupby(["condition", "detector"])["ap"].mean().unstack().round(3)
    print(piv.to_string())


if __name__ == "__main__":
    main()
