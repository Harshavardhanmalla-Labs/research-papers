#!/usr/bin/env python3
"""Entry point: run the Paper 13 policy-as-code evaluation across seeds 900 to 924."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from policyascode.model import (  # noqa: E402
    evaluate_seed, EVALUATION_SEEDS, RECURRENCE_GRID, REF_RECURRENCE,
    N_ENDPOINTS, HORIZON_DAYS, EMERGENT_RATE, BENIGN_RATE, BLOCK_RECALL, FALSE_POS,
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
        "evaluation_seeds": EVALUATION_SEEDS, "recurrence_grid": RECURRENCE_GRID,
        "ref_recurrence": REF_RECURRENCE, "n_endpoints": N_ENDPOINTS,
        "horizon_days": HORIZON_DAYS, "emergent_rate": EMERGENT_RATE,
        "benign_rate": BENIGN_RATE, "block_recall": BLOCK_RECALL, "false_pos": FALSE_POS,
        "n_rows": int(len(df)),
    }
    with open(args.output_dir / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print("\n=== Means at reference recurrence ===")
    ref = df[df.recurrence == REF_RECURRENCE]
    for c in ["reduction", "blockable_share", "ceiling_gap", "false_blocks_per_endpoint_month"]:
        print(f"  {c:34s} {ref[c].mean():.4f}")


if __name__ == "__main__":
    main()
