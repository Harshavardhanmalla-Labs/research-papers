"""Paper 9 self-trajectory evaluator.

For each cell K and each driving method m_drive, simulate W windows
where m_drive's top-K selection determines fleet evolution; at every
window record P@50 for ALL five scoring methods evaluated on the
current state.

Driving methods: {HygienePrio-full, EPSS-only, HRS-only, CVSS-only, Random}.
Scoring methods at each window: same 5.

Cell grid: K ∈ {50, 200}, λ = 3, W = 6, seeds 105..129.
Total rows: 2 * 5 * 5 * 25 * 6 = 7,500.
"""

from __future__ import annotations

import json
import sys
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
from hygieneprio.scorer import (  # noqa: E402
    HygienePrioScorer, ScorerWeights,
    EPSSOnlyScorer, CVSSOnlyScorer, HRSOnlyScorer, RandomScorer,
)
from hygieneprio.metrics import precision_at_k  # noqa: E402


CAPACITY_GRID = (50, 200)
LAMBDA = 3.0
N_WINDOWS = 6
EPSS_THRESHOLD = 0.10
HRS_PERCENTILE = 75
EVALUATION_SEEDS = tuple(range(105, 130))

FIXED_WEIGHTS = ScorerWeights(alpha=0.7, beta=0.5, gamma=0.1, delta=0.2)
HRS_WEIGHTS = HRSWeights(patch_posture=0.5, ad_exposure=0.3, telemetry_freshness=0.2)

METHODS = ("HygienePrio-full", "EPSS-only", "HRS-only", "CVSS-only", "Random")


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


def _rank_with_method(name: str, pairs: pd.DataFrame, hrs: pd.Series,
                       seed: int, window: int) -> pd.DataFrame:
    if name == "HygienePrio-full":
        return HygienePrioScorer(weights=FIXED_WEIGHTS).rank_pairs(pairs, hrs)
    if name == "EPSS-only":
        return EPSSOnlyScorer().rank_pairs(pairs)
    if name == "HRS-only":
        return HRSOnlyScorer().rank_pairs(pairs, hrs)
    if name == "CVSS-only":
        return CVSSOnlyScorer().rank_pairs(pairs)
    if name == "Random":
        return RandomScorer().rank_pairs(pairs, seed=seed * 100 + window)
    raise ValueError(name)


def _advance(state: FleetState, top_k_pairs: pd.DataFrame, *, w: int, seed: int) -> None:
    rng = np.random.default_rng((seed, w, 0))
    acted = apply_remediation(state, top_k_pairs)
    disclose_new_cves(state, rng, w, rate=LAMBDA)
    update_epss(state, rng)
    update_telemetry_freshness(state, acted)


def simulate(driver: str, K: int, seed: int) -> list[dict]:
    """Run one (driver, cell K, seed) trajectory; record all 5 scorers' P@50 each window."""
    state = _initial_state(seed)
    rows: list[dict] = []
    for w in range(1, N_WINDOWS + 1):
        pairs = applicable_pairs(state)
        hrs = _compute_hrs(state)
        pairs_l = pairs.copy()
        pairs_l["_label"] = _label(pairs_l, hrs)
        for m in METHODS:
            ranked = _rank_with_method(m, pairs_l, hrs, seed, w)
            rows.append({
                "cell_K": K, "cell_lambda": LAMBDA, "driver": driver,
                "scorer": m, "seed": seed, "window": w,
                "n_pairs": len(pairs_l), "n_positives": int(pairs_l["_label"].sum()),
                "p_at_50": round(float(precision_at_k(ranked["_label"].tolist(), 50)), 4),
            })
        if w < N_WINDOWS:
            driver_top = _rank_with_method(driver, pairs_l, hrs, seed, w).head(K)
            _advance(state, driver_top, w=w, seed=seed)
    return rows


def run(output_dir: Optional[Path] = None) -> pd.DataFrame:
    rows: list[dict] = []
    n_cells = len(CAPACITY_GRID)
    for ki, K in enumerate(CAPACITY_GRID, 1):
        for mi, driver in enumerate(METHODS, 1):
            print(f"[cell {ki}/{n_cells} K={K}, driver {mi}/5 {driver}]", flush=True)
            for s in EVALUATION_SEEDS:
                rows.extend(simulate(driver, K, s))
    df = pd.DataFrame(rows)
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / "self_traj_results.csv"
        df.to_csv(out, index=False)
        with open(output_dir / "run_manifest.json", "w") as f:
            json.dump({
                "capacity_grid": list(CAPACITY_GRID),
                "lambda": LAMBDA,
                "n_windows": N_WINDOWS,
                "methods": list(METHODS),
                "evaluation_seeds": list(EVALUATION_SEEDS),
                "n_rows": len(df),
            }, f, indent=2, default=float)
        print(f"Wrote {len(df)} rows to {out}")
    return df
