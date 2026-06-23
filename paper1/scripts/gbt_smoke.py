#!/usr/bin/env python3
"""GBT comparator smoke: fit LightGBM on synthetic, correlated data.

Reference comparator only — NOT a deployment recommendation. No real
experiment results; no scheduler, no metrics.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from paper1.model.gbt_comparator import (
    fit_gbt,
    load_gbt_config,
    predict_gbt,
    save_gbt_result,
)
from paper1.model.strategies import rank_pairs
from paper1.model.weights import FEATURE_COLUMNS

ARTIFACTS = Path(__file__).resolve().parent.parent / "data" / "artifacts"
SEED = 0
N = 300


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def _make_data():
    rng = np.random.default_rng(SEED)
    data: dict[str, list | np.ndarray] = {
        "pair_id": [f"P-{i:05d}" for i in range(N)],
        "cve_id": [f"CVE-2024-{1000 + (i % 50):04d}" for i in range(N)],
        "host_id": [f"H-{i:05d}" for i in range(N)],
    }
    for f in FEATURE_COLUMNS:
        data[f] = rng.random(N)
    ff = pd.DataFrame(data)
    z = (
        2.0 * ff["E"].to_numpy()
        + 1.5 * ff["C"].to_numpy()
        + 1.0 * ff["X"].to_numpy()
        - 1.5 * ff["R"].to_numpy()
        - 1.0
    )
    labels = pd.Series((rng.random(N) < _sigmoid(z)).astype(bool), dtype="boolean")
    base = date(2024, 6, 1)
    times = [base + timedelta(days=i) for i in range(N)]
    order = np.argsort([t.toordinal() for t in times])
    splits = [""] * N
    for rank, pos in enumerate(order):
        if rank < int(0.6 * N):
            splits[pos] = "train"
        elif rank < int(0.7 * N):
            splits[pos] = "gap"
        else:
            splits[pos] = "test"
    return ff, labels, pd.Series(splits), times


def main() -> int:
    ff, labels, splits, times = _make_data()
    cfg = load_gbt_config()
    model, result = fit_gbt(ff, labels, times, splits, config=cfg, seed=SEED)

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    save_gbt_result(result, ARTIFACTS / "gbt_smoke_result.json")

    preds = predict_gbt(model, ff)
    pair_frame = ff[["pair_id", "cve_id", "host_id"]].copy()
    ranked = rank_pairs("gbt_comparator", pair_frame, ff, gbt_model=model)

    print("=== GBT reference comparator (NOT a deployment recommendation) ===")
    print(f"  train size:        {result.train_size}")
    print(f"  positives/neg:     {result.positive_count} / {result.negative_count}")
    print(f"  selected iteration:{result.selected_iteration}")
    print(f"  validation scores: {result.validation_scores}")
    print(f"  prediction min/max:{preds.min():.4f} / {preds.max():.4f}")
    print("  top 5 pair IDs:")
    for _, r in ranked.head(5).iterrows():
        print(f"    #{r['rank']} {r['pair_id']}  score={r['priority_score']:.4f}")
    print("  NOTE: reference comparator only; the deployed model is the")
    print("        auditable linear scorer, not this GBT.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
