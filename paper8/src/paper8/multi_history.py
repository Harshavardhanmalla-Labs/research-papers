"""Paper 8 multi-window-history calibration evaluator.

At each (cell, window) we evaluate five strategies:
  fixed   — Paper 4 weights, never refit.
  lag1    — grid-search on calib seeds at window w-1 (Paper 7 baseline).
  trail3  — grid-search aggregating calib P@50 over windows
            max(1, w-3) .. w-1 with equal weights.
  ewma3   — same windows as trail3, weighted alpha^i with alpha=0.6
            (i=0 most recent past window).
  offline — grid-search at window w (Paper 7 offline-peek ceiling).

At w=1 all reduce to `fixed`.
"""

from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


_REPO_ROOT = Path(__file__).resolve().parents[3]
for _p in (_REPO_ROOT / "paper5" / "src", _REPO_ROOT / "paper4" / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from paper5.window_sim import (  # noqa: E402
    FleetState, applicable_pairs, apply_remediation,
    disclose_new_cves, update_epss, update_telemetry_freshness,
)
from hygieneprio.generator import EEHDAFleetGenerator  # noqa: E402
from hygieneprio.hrs import HygieneRiskScore, HRSWeights  # noqa: E402
from hygieneprio.scorer import HygienePrioScorer, ScorerWeights  # noqa: E402
from hygieneprio.metrics import precision_at_k  # noqa: E402


CAPACITY_GRID = (50, 100, 200)
LAMBDA = 3.0
N_WINDOWS = 6
EPSS_THRESHOLD = 0.10
HRS_PERCENTILE = 75

CALIBRATION_SEEDS = tuple(range(100, 105))
EVALUATION_SEEDS = tuple(range(105, 130))

FIXED_WEIGHTS = ScorerWeights(alpha=0.7, beta=0.5, gamma=0.1, delta=0.2)
HRS_WEIGHTS = HRSWeights(patch_posture=0.5, ad_exposure=0.3, telemetry_freshness=0.2)

GRID = {
    "alpha": [0.5, 0.7, 0.9],
    "beta":  [0.3, 0.5, 0.7],
    "gamma": [0.0, 0.1, 0.2],
    "delta": [0.0, 0.1, 0.2, 0.3],
}
GRID_CONFIGS = [
    ScorerWeights(alpha=a, beta=b, gamma=g, delta=d)
    for a, b, g, d in product(GRID["alpha"], GRID["beta"], GRID["gamma"], GRID["delta"])
]

EWMA_ALPHA = 0.6
TRAILING_HISTORY = 3


def _initial_state(seed: int) -> FleetState:
    t = EEHDAFleetGenerator(seed=seed).generate_all()
    return FleetState(
        vulnerability_records=t["vulnerability_records"],
        computers=t["computers"], users=t["users"], groups=t["groups"],
        group_membership_events=t["group_membership_events"],
        endpoint_patch_state=t["endpoint_patch_state"],
        telemetry_freshness_log=t["telemetry_freshness_log"],
    )


def _compute_hrs(state: FleetState) -> pd.Series:
    return HygieneRiskScore(weights=HRS_WEIGHTS).compute(
        endpoint_patch_state=state.endpoint_patch_state,
        vulnerability_records=state.vulnerability_records,
        users=state.users, groups=state.groups,
        group_membership_events=state.group_membership_events,
        computers=state.computers,
        telemetry_freshness_log=state.telemetry_freshness_log,
    )


def _label(pairs: pd.DataFrame, hrs: pd.Series) -> pd.Series:
    if len(pairs) == 0:
        return pd.Series([], dtype=int)
    thr = hrs.quantile(HRS_PERCENTILE / 100.0)
    return ((pairs["epss_score"] > EPSS_THRESHOLD) & (pairs["computer_id"].map(hrs) > thr)).astype(int)


def _score_p50(pairs: pd.DataFrame, hrs: pd.Series, sw: ScorerWeights) -> float:
    if len(pairs) == 0:
        return 0.0
    pl = pairs.copy()
    pl["_label"] = _label(pl, hrs)
    ranked = HygienePrioScorer(weights=sw).rank_pairs(pl, hrs)
    return float(precision_at_k(ranked["_label"].tolist(), 50))


def _advance(state: FleetState, top_k_pairs: pd.DataFrame, *, w: int, seed: int) -> None:
    rng = np.random.default_rng((seed, w, 0))
    acted = apply_remediation(state, top_k_pairs)
    disclose_new_cves(state, rng, w, rate=LAMBDA)
    update_epss(state, rng)
    update_telemetry_freshness(state, acted)


def _cache_states(seeds: list[int], K: int) -> dict[int, list[tuple[pd.DataFrame, pd.Series]]]:
    """Drive each seed through W windows with fixed-weight HP-full policy.

    Returns {seed: [(pairs_w1, hrs_w1), ..., (pairs_W, hrs_W)]}.
    """
    out: dict[int, list[tuple[pd.DataFrame, pd.Series]]] = {}
    for seed in seeds:
        state = _initial_state(seed)
        windows = []
        for w in range(1, N_WINDOWS + 1):
            pairs = applicable_pairs(state)
            hrs = _compute_hrs(state)
            windows.append((pairs.reset_index(drop=True), hrs))
            if w < N_WINDOWS:
                pl = pairs.copy()
                pl["_label"] = _label(pl, hrs)
                ranked = HygienePrioScorer(weights=FIXED_WEIGHTS).rank_pairs(pl, hrs)
                _advance(state, ranked.head(K), w=w, seed=seed)
        out[seed] = windows
    return out


def _best_weights_weighted(
    states_by_window: list[list[tuple[pd.DataFrame, pd.Series]]],
    weights_per_window: list[float],
) -> ScorerWeights:
    """Grid-search weights to maximise weighted-mean P@50 across the
    provided per-window calibration-state lists.

    states_by_window: list of lists, outer index = trailing-window
      slot (0 = most recent past, 1 = one earlier, ...). Inner list
      = (pairs, hrs) for the 5 calibration seeds.
    weights_per_window: must match outer length; need not sum to 1.
    """
    assert len(states_by_window) == len(weights_per_window)
    total_w = sum(weights_per_window)
    weights = np.array(weights_per_window) / total_w  # normalise

    best, best_m = FIXED_WEIGHTS, -1.0
    for sw in GRID_CONFIGS:
        per_window_means = []
        for states in states_by_window:
            per_window_means.append(np.mean([_score_p50(p, h, sw) for (p, h) in states]))
        m = float(np.dot(weights, per_window_means))
        if m > best_m:
            best_m, best = m, sw
    return best


def run_cell(K: int) -> pd.DataFrame:
    print(f"[K={K}] caching calibration states...")
    calib = _cache_states(list(CALIBRATION_SEEDS), K)
    print(f"[K={K}] caching evaluation states...")
    eval_ = _cache_states(list(EVALUATION_SEEDS), K)

    rows: list[dict] = []
    for w_idx in range(N_WINDOWS):
        w = w_idx + 1
        sw_fixed = FIXED_WEIGHTS
        if w == 1:
            sw_lag1 = sw_trail3 = sw_ewma3 = sw_offline = FIXED_WEIGHTS
        else:
            # lag1: just the (w-1) state
            lag1_states = [[calib[s][w_idx - 1] for s in CALIBRATION_SEEDS]]
            sw_lag1 = _best_weights_weighted(lag1_states, [1.0])

            # Trailing window: max(1, w-3)..w-1 inclusive
            start_idx = max(0, w_idx - TRAILING_HISTORY)
            window_indices = list(range(start_idx, w_idx))  # 0-indexed past windows
            assert len(window_indices) >= 1

            trail_states = [
                [calib[s][i] for s in CALIBRATION_SEEDS]
                for i in window_indices
            ]
            sw_trail3 = _best_weights_weighted(
                trail_states, [1.0] * len(window_indices)
            )

            # EWMA: most-recent past window gets weight alpha^0 = 1,
            # one earlier gets alpha^1, etc. Reverse window_indices so the
            # most-recent past is index 0 in the weights.
            ewma_states = list(reversed(trail_states))
            ewma_weights = [EWMA_ALPHA ** i for i in range(len(window_indices))]
            sw_ewma3 = _best_weights_weighted(ewma_states, ewma_weights)

            # offline-peek: the current window state on calib seeds
            offline_states = [[calib[s][w_idx] for s in CALIBRATION_SEEDS]]
            sw_offline = _best_weights_weighted(offline_states, [1.0])

        for s in EVALUATION_SEEDS:
            pairs, hrs = eval_[s][w_idx]
            for tag, sw in (("fixed", sw_fixed), ("lag1", sw_lag1),
                            ("trail3", sw_trail3), ("ewma3", sw_ewma3),
                            ("offline", sw_offline)):
                rows.append({
                    "cell_K": K, "cell_lambda": LAMBDA,
                    "seed": s, "window": w, "strategy": tag,
                    "p_at_50": round(_score_p50(pairs, hrs, sw), 4),
                    "alpha": sw.alpha, "beta": sw.beta,
                    "gamma": sw.gamma, "delta": sw.delta,
                })
        print(f"  W{w}: lag1={sw_lag1.alpha:.1f}/{sw_lag1.beta:.1f}/{sw_lag1.gamma:.1f}/{sw_lag1.delta:.1f} "
              f"ewma3={sw_ewma3.alpha:.1f}/{sw_ewma3.beta:.1f}/{sw_ewma3.gamma:.1f}/{sw_ewma3.delta:.1f}",
              flush=True)
    return pd.DataFrame(rows)


def run(output_dir: Optional[Path] = None) -> pd.DataFrame:
    frames = [run_cell(K) for K in CAPACITY_GRID]
    df = pd.concat(frames, ignore_index=True)
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / "multi_history_results.csv"
        df.to_csv(out, index=False)
        with open(output_dir / "run_manifest.json", "w") as f:
            json.dump({
                "capacity_grid": list(CAPACITY_GRID),
                "lambda": LAMBDA,
                "n_windows": N_WINDOWS,
                "strategies": ["fixed", "lag1", "trail3", "ewma3", "offline"],
                "ewma_alpha": EWMA_ALPHA,
                "trailing_history": TRAILING_HISTORY,
                "grid_size": len(GRID_CONFIGS),
                "calibration_seeds": list(CALIBRATION_SEEDS),
                "evaluation_seeds": list(EVALUATION_SEEDS),
                "n_rows": len(df),
            }, f, indent=2, default=float)
        print(f"Wrote {len(df)} rows to {out}")
    return df
