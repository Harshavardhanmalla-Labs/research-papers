#!/usr/bin/env python3
"""Calibration smoke: fit logit + ridge weights on synthetic, correlated data.

No real experiment results. Writes calibration artifacts to data/artifacts/
and registers the calibrated weights in the runtime registry.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from paper1.model.linear_model import (
    fit_weights_linear,
    fit_weights_logit,
    register_calibrated_weights,
    save_calibration_result,
)
from paper1.model.scoring import score_pairs_linear
from paper1.model.weights import FEATURE_COLUMNS, get_weights

ARTIFACTS = Path(__file__).resolve().parent.parent / "data" / "artifacts"
SEED = 0
N = 300


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def _make_data():
    rng = np.random.default_rng(SEED)
    data: dict[str, list | np.ndarray] = {"pair_id": [f"P-{i:05d}" for i in range(N)]}
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

    logit = fit_weights_logit(ff, labels, times, splits, seed=SEED)
    ridge = fit_weights_linear(ff, labels, times, splits, seed=SEED)

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    save_calibration_result(logit, ARTIFACTS / "calibration_smoke_logit.json")
    save_calibration_result(ridge, ARTIFACTS / "calibration_smoke_ridge.json")

    register_calibrated_weights(logit, "w_logit_calibrated")
    register_calibrated_weights(ridge, "w_lin_calibrated")

    print("=== logit ===")
    print(f"  selected C:      {logit.selected_hyperparameter}")
    print(f"  train size:      {logit.train_size}")
    print(f"  positives/neg:   {logit.positive_count} / {logit.negative_count}")
    print(f"  clipped:         {logit.clipped_features}")
    print(f"  weights:         { {k: round(v, 4) for k, v in logit.weights.items()} }")
    print("=== ridge ===")
    print(f"  selected alpha:  {ridge.selected_hyperparameter}")
    print(f"  weights:         { {k: round(v, 4) for k, v in ridge.weights.items()} }")

    scored = score_pairs_linear(ff.head(3), get_weights("w_logit_calibrated"))
    print("=== sample scores (w_logit_calibrated) ===")
    for _, r in scored.iterrows():
        print(f"  {r['pair_id']}  score={r['priority_score']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
