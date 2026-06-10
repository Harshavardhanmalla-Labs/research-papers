"""CLI entry for the Paper 10 AutoHeal evaluation."""
from __future__ import annotations
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]

from autoheal.framework import AutoHeal, AutoHealConfig
from autoheal.baselines import simulate_human_in_loop, simulate_fixed_policy


CAP_GRID = (50, 100, 200)
LAM = 3.0
EVAL_SEEDS = tuple(range(105, 130))
REAL_CORPUS = REPO / "real_data" / "processed" / "cve_corpus_for_sampling.csv"


def _to_rows(outcomes, strategy: str) -> list[dict]:
    return [{**asdict(o), "strategy": strategy} for o in outcomes]


def main() -> None:
    out_dir = REPO / "paper10" / "results" / "primary_v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for K in CAP_GRID:
        cfg = AutoHealConfig(capacity=K, arrival_rate=LAM,
                             use_real_corpus=True, real_corpus_path=REAL_CORPUS)
        autoheal = AutoHeal(cfg)
        print(f"K={K}: AutoHeal...", flush=True)
        for s in EVAL_SEEDS:
            rows.extend(_to_rows(autoheal.simulate(s), "AutoHeal"))
        print(f"K={K}: Human-in-loop...", flush=True)
        for s in EVAL_SEEDS:
            rows.extend(_to_rows(simulate_human_in_loop(s, cfg), "Human-in-loop"))
        print(f"K={K}: Fixed-policy...", flush=True)
        for s in EVAL_SEEDS:
            rows.extend(_to_rows(simulate_fixed_policy(s, cfg), "Fixed-policy"))
    df = pd.DataFrame(rows)
    out_csv = out_dir / "autoheal_results.csv"
    df.to_csv(out_csv, index=False)
    with open(out_dir / "run_manifest.json", "w") as f:
        json.dump({
            "capacity_grid": list(CAP_GRID),
            "lambda": LAM,
            "n_windows": 12,
            "evaluation_seeds": list(EVAL_SEEDS),
            "strategies": ["AutoHeal", "Human-in-loop", "Fixed-policy"],
            "real_corpus": str(REAL_CORPUS),
            "n_rows": len(df),
        }, f, indent=2, default=float)
    print(f"Wrote {len(df)} rows to {out_csv}")


if __name__ == "__main__":
    main()
