"""Paper 10 adaptive change-point calibration evaluator.

Five strategies at every (cell, window):
  fixed    — Paper 4 weights, no refit.
  lag1     — Grid-search on calib seeds at w-1 (Paper 7 baseline).
  adaptive — lag-1 weights if change-point detector returns False;
             otherwise fall back to fixed.
  gated    — capacity-conditional static rule: lag-1 weights if K<=100,
             fixed if K>=200. Acts as a non-adaptive control.
  offline  — Grid-search at w (Paper 7 ceiling).

Change-point detector at window w >= 2:
  Compute candidate lag-1 weights from calib seeds at w-1.
  Compare mean calibration-seed P@50 at w-1 vs w-2 (or fixed-W1 at w=2).
  Fire if |delta| >= TAU = 0.05.
"""

from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path
from typing import Iterable, Optional

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
TAU = 0.05                  # change-point detection threshold (pre-registered)
GATED_K_THRESHOLD = 100     # capacity at or below this -> use lag1 in `gated`

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


def _grid_search(states_per_seed: list[tuple[pd.DataFrame, pd.Series]]) -> tuple[ScorerWeights, float]:
    best, best_m = FIXED_WEIGHTS, -1.0
    for sw in GRID_CONFIGS:
        m = float(np.mean([_score_p50(p, h, sw) for (p, h) in states_per_seed]))
        if m > best_m:
            best_m, best = m, sw
    return best, best_m


def run_cell(K: int) -> tuple[pd.DataFrame, list[dict]]:
    print(f"[K={K}] caching calibration states...")
    calib = _cache_states(list(CALIBRATION_SEEDS), K)
    print(f"[K={K}] caching evaluation states...")
    eval_ = _cache_states(list(EVALUATION_SEEDS), K)

    rows: list[dict] = []
    cp_log: list[dict] = []

    for w_idx in range(N_WINDOWS):
        w = w_idx + 1
        sw_fixed = FIXED_WEIGHTS

        if w == 1:
            sw_lag1 = sw_adaptive = sw_offline = FIXED_WEIGHTS
            cp_fired = False
            cp_delta = 0.0
        else:
            # lag-1 fit on calib seeds at w-1
            lag1_states = [calib[s][w_idx - 1] for s in CALIBRATION_SEEDS]
            sw_lag1, lag1_mean_at_wm1 = _grid_search(lag1_states)

            # Change-point comparison: lag1-fit weights' P@50 at w-1 vs w-2
            if w == 2:
                # Compare lag1-fit at w-1 vs fixed-weight P@50 at w-1
                # (no w-2 state; baseline is the previous-regime fixed score)
                fixed_at_wm1 = float(np.mean(
                    [_score_p50(p, h, FIXED_WEIGHTS) for (p, h) in lag1_states]
                ))
                cp_delta = lag1_mean_at_wm1 - fixed_at_wm1
            else:
                wm2_states = [calib[s][w_idx - 2] for s in CALIBRATION_SEEDS]
                # Score lag1-fit weights at w-2 calibration state
                lag1_at_wm2 = float(np.mean(
                    [_score_p50(p, h, sw_lag1) for (p, h) in wm2_states]
                ))
                cp_delta = lag1_mean_at_wm1 - lag1_at_wm2

            cp_fired = abs(cp_delta) >= TAU
            sw_adaptive = FIXED_WEIGHTS if cp_fired else sw_lag1

            # Offline: grid-search at calib seeds' current w state
            off_states = [calib[s][w_idx] for s in CALIBRATION_SEEDS]
            sw_offline, _ = _grid_search(off_states)

        # Gated: static capacity-conditional rule
        if K <= GATED_K_THRESHOLD:
            sw_gated = sw_lag1
        else:
            sw_gated = sw_fixed

        cp_log.append({
            "cell_K": K, "window": w, "cp_delta": round(cp_delta, 4),
            "cp_fired": cp_fired,
            "sw_adaptive": (sw_adaptive.alpha, sw_adaptive.beta, sw_adaptive.gamma, sw_adaptive.delta),
        })

        for s in EVALUATION_SEEDS:
            pairs, hrs = eval_[s][w_idx]
            for tag, sw in (("fixed", sw_fixed), ("lag1", sw_lag1),
                            ("adaptive", sw_adaptive), ("gated", sw_gated),
                            ("offline", sw_offline)):
                rows.append({
                    "cell_K": K, "cell_lambda": LAMBDA,
                    "seed": s, "window": w, "strategy": tag,
                    "p_at_50": round(_score_p50(pairs, hrs, sw), 4),
                    "alpha": sw.alpha, "beta": sw.beta,
                    "gamma": sw.gamma, "delta": sw.delta,
                    "cp_fired": cp_fired,
                })
        print(f"  W{w}: cp_delta={cp_delta:+.3f} fired={cp_fired}", flush=True)

    return pd.DataFrame(rows), cp_log


def run(output_dir: Optional[Path] = None) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    cp_logs: list[dict] = []
    for K in CAPACITY_GRID:
        df, cp = run_cell(K)
        frames.append(df)
        cp_logs.extend(cp)
    df = pd.concat(frames, ignore_index=True)

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / "adaptive_results.csv"
        df.to_csv(out, index=False)
        pd.DataFrame(cp_logs).to_csv(output_dir / "changepoint_log.csv", index=False)
        with open(output_dir / "run_manifest.json", "w") as f:
            json.dump({
                "capacity_grid": list(CAPACITY_GRID),
                "lambda": LAMBDA,
                "n_windows": N_WINDOWS,
                "tau": TAU,
                "gated_K_threshold": GATED_K_THRESHOLD,
                "strategies": ["fixed", "lag1", "adaptive", "gated", "offline"],
                "grid_size": len(GRID_CONFIGS),
                "calibration_seeds": list(CALIBRATION_SEEDS),
                "evaluation_seeds": list(EVALUATION_SEEDS),
                "n_rows": len(df),
            }, f, indent=2, default=float)
        print(f"Wrote {len(df)} rows to {out}")
    return df
