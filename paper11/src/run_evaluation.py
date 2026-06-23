#!/usr/bin/env python3
"""
Entry point: run the full CAP-G (Paper 11) evaluation.

Pipeline (PAPER11_PROTOCOL.md):
  1. Calibrate rho on 5 held-out calibration seeds (objective: mean MWP@50).
  2. Primary evaluation on 25 heterogeneous-fleet seeds (200-224), all methods.
  3. Homogeneous-fleet control (H3 mechanism test).

Writes primary_results.csv, homogeneous_control.csv, run_manifest.json.
All EPSS/KEV signal is resampled from the real corpus in real_data/processed/.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from capg.evaluate import (  # noqa: E402
    run_evaluation, run_homogeneous_control, calibrate_rho,
    EVALUATION_SEEDS, CALIBRATION_SEEDS, K_VALUES, RHO_GRID, REAL_CORPUS,
)


def main() -> None:
    ap = argparse.ArgumentParser(description="Run CAP-G (Paper 11) evaluation.")
    ap.add_argument("--output-dir", type=Path,
                    default=Path(__file__).parent.parent / "results" / "primary_v1")
    ap.add_argument("--corpus", type=Path, default=REAL_CORPUS)
    ap.add_argument("--rho", type=float, default=None,
                    help="Override calibrated rho (skips calibration).")
    args = ap.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    corpus = pd.read_csv(args.corpus)
    print(f"Loaded real corpus: {len(corpus):,} CVEs from {args.corpus}")

    # --- Step 1: calibrate rho ---
    if args.rho is None:
        print("Calibrating rho on held-out seeds...")
        calib = calibrate_rho(corpus)
        rho = calib["selected_rho"]
        print(f"  selected rho={rho} (cal MWP@50={calib['selected_mwp50']}, "
              f"gain over HygienePrio={calib['calibration_gain_pp']}pp)")
    else:
        rho = args.rho
        calib = {"selected_rho": rho, "note": "rho overridden via --rho"}

    # --- Step 2: primary heterogeneous evaluation ---
    print(f"Primary evaluation: {len(EVALUATION_SEEDS)} heterogeneous seeds, rho={rho}")
    df = run_evaluation(rho, corpus)
    df.to_csv(args.output_dir / "primary_results.csv", index=False)
    print(f"Wrote {len(df)} rows -> primary_results.csv")

    # --- Step 3: homogeneous control (H3) ---
    print("Homogeneous-fleet control (H3)...")
    df_hom = run_homogeneous_control(rho, corpus)
    df_hom.to_csv(args.output_dir / "homogeneous_control.csv", index=False)
    print(f"Wrote {len(df_hom)} rows -> homogeneous_control.csv")

    # --- Manifest ---
    manifest = {
        "evaluation_seeds": EVALUATION_SEEDS,
        "calibration_seeds": CALIBRATION_SEEDS,
        "k_values": K_VALUES,
        "rho_grid": RHO_GRID,
        "selected_rho": rho,
        "calibration": calib,
        "real_corpus": str(args.corpus),
        "n_corpus_cves": int(len(corpus)),
        "acs_weights": {"crit": 0.5, "zone": 0.3, "sens": 0.2},
        "hygieneprio_weights": {"alpha": 0.7, "beta": 0.5, "gamma": 0.1, "delta": 0.2},
        "n_rows_primary": int(len(df)),
        "n_rows_homogeneous": int(len(df_hom)),
        "methods": sorted(df["method"].unique().tolist()),
    }
    with open(args.output_dir / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # --- Quick console summary ---
    print("\n=== Mean MWP@50 by method (heterogeneous) ===")
    summ = df.groupby("method")["mwp_at_50"].mean().sort_values(ascending=False)
    print(summ.round(4).to_string())
    print("\nDone. All fleets are synthetic; EPSS/KEV signal is from the real corpus.")


if __name__ == "__main__":
    main()
