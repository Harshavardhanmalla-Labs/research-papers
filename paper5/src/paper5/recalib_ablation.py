"""H3 ablation: per-window weight recalibration vs the fixed weights.

For each window w in 1..W, fit ScorerWeights by grid search on the 5
calibration seeds' Window-w state to maximise mean P@50, then apply those
weights to the 25 evaluation seeds at the same window. Compare to the
fixed-weight HygienePrio-full P@50.

Pre-registered stop rule (PAPER5_PROTOCOL.md, H4 / paper §7):
  If max over windows of (recalibrated - fixed) at P@50 is < 5 pp,
  declare per-window recalibration uninformative.
"""

from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

PAPER5_ROOT = Path(__file__).resolve().parents[2]   # .../paper5
REPO_ROOT = PAPER5_ROOT.parent                       # .../Research Papers
sys.path.insert(0, str(REPO_ROOT / "paper4" / "src"))

from hygieneprio.hrs import HygieneRiskScore, HRSWeights  # noqa: E402
from hygieneprio.scorer import HygienePrioScorer, ScorerWeights  # noqa: E402
from hygieneprio.metrics import precision_at_k  # noqa: E402

from .temporal_eval import (
    CALIBRATION_SEEDS,
    EVALUATION_SEEDS,
    HRS_WEIGHTS,
    N_WINDOWS,
    SELECTION_K,
    _compute_hrs,
    _initial_state,
    _label_pairs,
)
from .window_sim import advance_window, applicable_pairs


# Coarse grid (matches paper4 calibration density).
GRID = {
    "alpha": [0.5, 0.7, 0.9],
    "beta":  [0.3, 0.5, 0.7],
    "gamma": [0.0, 0.1, 0.2],
    "delta": [0.0, 0.1, 0.2, 0.3],
}


def _evaluate_weights_on_pairs(pairs: pd.DataFrame, hrs: pd.Series, sw: ScorerWeights) -> float:
    if len(pairs) == 0:
        return 0.0
    pairs = pairs.copy()
    pairs["_label"] = _label_pairs(pairs, hrs)
    scorer = HygienePrioScorer(weights=sw)
    ranked = scorer.rank_pairs(pairs, hrs)
    return precision_at_k(ranked["_label"].tolist(), 50)


def _per_window_states(seeds: list[int]) -> dict[int, list[tuple[pd.DataFrame, pd.Series]]]:
    """Return {seed: [(pairs_w1, hrs_w1), ..., (pairs_W, hrs_W)]} using the
    HygienePrio-full fixed-weight policy to drive evolution (matches the
    primary evaluation in temporal_eval)."""
    out: dict[int, list[tuple[pd.DataFrame, pd.Series]]] = {}
    fixed = ScorerWeights(alpha=0.7, beta=0.5, gamma=0.1, delta=0.2)

    for seed in seeds:
        state = _initial_state(seed)
        windows: list[tuple[pd.DataFrame, pd.Series]] = []
        for w in range(1, N_WINDOWS + 1):
            pairs = applicable_pairs(state)
            hrs = _compute_hrs(state)
            windows.append((pairs.reset_index(drop=True), hrs))
            if w < N_WINDOWS:
                # Fixed-weight policy drives evolution.
                pl = pairs.copy()
                pl["_label"] = _label_pairs(pl, hrs)
                ranked = HygienePrioScorer(weights=fixed).rank_pairs(pl, hrs)
                advance_window(state, ranked.head(SELECTION_K), window_index=w, seed=seed)
        out[seed] = windows
    return out


def run() -> pd.DataFrame:
    print("Caching per-window states for calibration seeds...")
    calib_states = _per_window_states(list(CALIBRATION_SEEDS))
    print("Caching per-window states for evaluation seeds...")
    eval_states = _per_window_states(list(EVALUATION_SEEDS))

    rows = []
    fixed = ScorerWeights(alpha=0.7, beta=0.5, gamma=0.1, delta=0.2)
    grid_configs = [
        ScorerWeights(alpha=a, beta=b, gamma=g, delta=d)
        for a, b, g, d in product(GRID["alpha"], GRID["beta"], GRID["gamma"], GRID["delta"])
    ]

    for w_idx in range(N_WINDOWS):
        w = w_idx + 1
        # Pick best weights on calibration seeds at this window
        best_sw, best_mean = None, -1.0
        for sw in grid_configs:
            vals = [
                _evaluate_weights_on_pairs(p, h, sw)
                for (p, h) in (calib_states[s][w_idx] for s in CALIBRATION_SEEDS)
            ]
            m = float(np.mean(vals))
            if m > best_mean:
                best_mean, best_sw = m, sw

        # Apply both fixed and recalibrated on evaluation seeds at this window
        fixed_p50 = np.mean([
            _evaluate_weights_on_pairs(p, h, fixed)
            for (p, h) in (eval_states[s][w_idx] for s in EVALUATION_SEEDS)
        ])
        recal_p50 = np.mean([
            _evaluate_weights_on_pairs(p, h, best_sw)
            for (p, h) in (eval_states[s][w_idx] for s in EVALUATION_SEEDS)
        ])

        rows.append({
            "window": w,
            "fixed_p50": round(float(fixed_p50), 4),
            "recalibrated_p50": round(float(recal_p50), 4),
            "delta": round(float(recal_p50 - fixed_p50), 4),
            "best_alpha": best_sw.alpha,
            "best_beta":  best_sw.beta,
            "best_gamma": best_sw.gamma,
            "best_delta": best_sw.delta,
        })
        print(f"  W{w}: fixed={fixed_p50:.3f}  recal={recal_p50:.3f}  Δ={recal_p50-fixed_p50:+.3f}")

    df = pd.DataFrame(rows)
    out_dir = PAPER5_ROOT / "results" / "primary_full_v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "recalibration_ablation.csv", index=False)
    max_delta = df["delta"].max()
    summary = {
        "max_delta_p50": float(max_delta),
        "stop_rule_threshold_pp": 0.05,
        "recalibration_helps": bool(max_delta >= 0.05),
    }
    with open(out_dir / "recalibration_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nmax Δ = {max_delta:+.3f}  →  recalibration uninformative: {max_delta < 0.05}")
    return df


if __name__ == "__main__":
    run()
