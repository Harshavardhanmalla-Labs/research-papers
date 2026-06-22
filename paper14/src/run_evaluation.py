#!/usr/bin/env python3
"""
Entry point: run the full PTI (Paper 14) evaluation across the noise sweep.

Writes primary_results.csv (25 seeds x 5 sigma x 9 methods) and run_manifest.json.
EPSS/KEV maturation is grounded in the real corpus in real_data/processed/.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from pti.model import (  # noqa: E402
    evaluate_seed, EVALUATION_SEEDS, SIGMA_GRID, K_VALUES, REF_SIGMA,
    REAL_CORPUS, METHODS, BIAS_B, TAU, P_KEV_OBS, KEV_BONUS, RHO,
)


def main() -> None:
    ap = argparse.ArgumentParser(description="Run PTI (Paper 14) evaluation.")
    ap.add_argument("--output-dir", type=Path,
                    default=Path(__file__).parent.parent / "results" / "primary_v1")
    ap.add_argument("--corpus", type=Path, default=REAL_CORPUS)
    args = ap.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    corpus = pd.read_csv(args.corpus)
    print(f"Loaded real corpus: {len(corpus):,} CVEs")

    rows = []
    for seed in EVALUATION_SEEDS:
        print(f"  seed {seed}...", end=" ", flush=True)
        rows.extend(evaluate_seed(seed, corpus))
        print("done")
    df = pd.DataFrame(rows)
    df.to_csv(args.output_dir / "primary_results.csv", index=False)
    print(f"Wrote {len(df)} rows -> primary_results.csv")

    manifest = {
        "evaluation_seeds": EVALUATION_SEEDS,
        "sigma_grid": SIGMA_GRID,
        "reference_sigma": REF_SIGMA,
        "k_values": K_VALUES,
        "methods": METHODS,
        "observation_model": {"bias_b": BIAS_B, "tau": TAU, "p_kev_obs": P_KEV_OBS,
                              "kev_bonus": KEV_BONUS},
        "pti_estimator": "precision-weighted logit fusion (inverse-variance)",
        "rho": RHO,
        "real_corpus": str(args.corpus),
        "n_corpus_cves": int(len(corpus)),
        "n_rows": int(len(df)),
    }
    with open(args.output_dir / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n=== Mean MWP@50 at reference sigma={REF_SIGMA} ===")
    ref = df[df.sigma == REF_SIGMA].groupby("method")["mwp_at_50"].mean().sort_values(ascending=False)
    print(ref.round(4).to_string())


if __name__ == "__main__":
    main()
