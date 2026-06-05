"""Paper 7 online-calibration evaluator.

At each (cell, window) and for each of three strategies
(`fixed`, `online`, `offline`), compute P@50 on the 25 evaluation seeds.

The evolution policy is the Paper 5 / 6 convention: HygienePrio-full
under the strategy's *fixed* Paper-4 weights drives the fleet trajectory
for ALL strategies. This avoids non-identifiable cross-strategy
trajectories and isolates the scoring decision from the fleet-evolution
decision (a known limitation acknowledged in the threats section of the
paper).

Three strategies:
  - `fixed`:   never refit; use Paper-4 weights every window.
  - `online`:  at window w >= 2, grid-search on calibration seeds at
               window w-1 (no current-window peek).
  - `offline`: at window w >= 2, grid-search on calibration seeds at
               window w (peek; matches Paper 5 H3 ablation).
At W1, all three strategies reduce to `fixed`.
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
_PAPER5_SRC = _REPO_ROOT / "paper5" / "src"
_PAPER4_SRC = _REPO_ROOT / "paper4" / "src"
for _p in (_PAPER5_SRC, _PAPER4_SRC):
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


# ---------------------------------------------------------------------------
# Pre-registered constants (PAPER7_PROTOCOL.md)
# ---------------------------------------------------------------------------

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


def _cache_per_window_states(seeds: list[int], K: int) -> dict[int, list[tuple[pd.DataFrame, pd.Series]]]:
    """Drive each seed's fleet through W windows with fixed-weight HP-full
    top-K policy, caching (pairs, hrs) per window."""
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


def _best_weights(states: list[tuple[pd.DataFrame, pd.Series]]) -> ScorerWeights:
    """Grid-search weights to maximise mean P@50 across the given (pairs, hrs)
    states. Used for both `online` (states = window w-1) and `offline`
    (states = window w)."""
    best, best_m = FIXED_WEIGHTS, -1.0
    for sw in GRID_CONFIGS:
        m = float(np.mean([_score_p50(p, h, sw) for (p, h) in states]))
        if m > best_m:
            best_m, best = m, sw
    return best


def run_cell(K: int) -> pd.DataFrame:
    """Run all three calibration strategies for one capacity K."""
    print(f"[K={K}] caching calibration-seed states...")
    calib_windows = _cache_per_window_states(list(CALIBRATION_SEEDS), K)
    print(f"[K={K}] caching evaluation-seed states...")
    eval_windows = _cache_per_window_states(list(EVALUATION_SEEDS), K)

    rows: list[dict] = []
    for w_idx in range(N_WINDOWS):
        w = w_idx + 1

        # Determine the weights for each strategy at this window.
        sw_fixed = FIXED_WEIGHTS
        if w == 1:
            sw_online = FIXED_WEIGHTS
            sw_offline = FIXED_WEIGHTS
        else:
            online_states = [calib_windows[s][w_idx - 1] for s in CALIBRATION_SEEDS]
            offline_states = [calib_windows[s][w_idx] for s in CALIBRATION_SEEDS]
            sw_online = _best_weights(online_states)
            sw_offline = _best_weights(offline_states)

        # Apply each strategy's weights to every eval seed at window w.
        for s in EVALUATION_SEEDS:
            pairs, hrs = eval_windows[s][w_idx]
            for tag, sw in (("fixed", sw_fixed),
                           ("online", sw_online),
                           ("offline", sw_offline)):
                rows.append({
                    "cell_K": K, "cell_lambda": LAMBDA,
                    "seed": s, "window": w, "strategy": tag,
                    "p_at_50": round(_score_p50(pairs, hrs, sw), 4),
                    "alpha": sw.alpha, "beta": sw.beta,
                    "gamma": sw.gamma, "delta": sw.delta,
                })
        print(f"  W{w}: online weights = {sw_online}; offline = {sw_offline}", flush=True)

    return pd.DataFrame(rows)


def run(output_dir: Optional[Path] = None) -> pd.DataFrame:
    frames = [run_cell(K) for K in CAPACITY_GRID]
    df = pd.concat(frames, ignore_index=True)
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / "online_calib_results.csv"
        df.to_csv(out, index=False)
        with open(output_dir / "run_manifest.json", "w") as f:
            json.dump({
                "capacity_grid": list(CAPACITY_GRID),
                "lambda": LAMBDA,
                "n_windows": N_WINDOWS,
                "calibration_seeds": list(CALIBRATION_SEEDS),
                "evaluation_seeds": list(EVALUATION_SEEDS),
                "grid_size": len(GRID_CONFIGS),
                "n_rows": len(df),
            }, f, indent=2, default=float)
        print(f"Wrote {len(df)} rows to {out}")
    return df
