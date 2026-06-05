"""Paper 6 sweep evaluation: extend Paper 5's multi-window simulator
across a (capacity K, arrival rate lambda) grid.

For each (K, lambda) cell, for each evaluation seed s in 105..129, for each
window w in 1..W:
  1. Recompute HRS from the current fleet state.
  2. Label pairs (per-window ground truth).
  3. Score with all 5 methods.
  4. Compute P@K' for K' in {50, 100, 250} (note: K' is the metric K, NOT
     the cell's capacity K; capacity controls fleet evolution only).
  5. Advance the fleet by remediating HygienePrio-full's top-K pairs and
     by drawing Poisson(lambda) new CVE disclosures.

The sweep is deterministic from the seed list. Locked grid:
  K     in {10, 25, 50, 100, 200}
  lambda in {1, 3, 6, 12}
Total: 20 cells x 25 seeds x 6 windows x 5 methods = 15,000 rows.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Path wiring: pull in paper5 (for the simulator) and paper4 (for scorers).
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PAPER5_SRC = _REPO_ROOT / "paper5" / "src"
_PAPER4_SRC = _REPO_ROOT / "paper4" / "src"
for _p in (_PAPER5_SRC, _PAPER4_SRC):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from paper5 import window_sim as ws  # noqa: E402
from paper5.window_sim import (  # noqa: E402
    FleetState,
    applicable_pairs,
    apply_remediation,
    update_epss,
    update_telemetry_freshness,
    disclose_new_cves,
)
from hygieneprio.generator import EEHDAFleetGenerator  # noqa: E402
from hygieneprio.hrs import HygieneRiskScore, HRSWeights  # noqa: E402
from hygieneprio.scorer import (  # noqa: E402
    HygienePrioScorer,
    ScorerWeights,
    EPSSOnlyScorer,
    CVSSOnlyScorer,
    HRSOnlyScorer,
    RandomScorer,
)
from hygieneprio.metrics import precision_at_k  # noqa: E402


# ---------------------------------------------------------------------------
# Pre-registered constants (PAPER6_PROTOCOL.md)
# ---------------------------------------------------------------------------

CAPACITY_GRID = (10, 25, 50, 100, 200)
LAMBDA_GRID = (1.0, 3.0, 6.0, 12.0)
N_WINDOWS = 6
METRIC_KS = (50, 100, 250)
EPSS_THRESHOLD = 0.10
HRS_PERCENTILE = 75

EVALUATION_SEEDS = tuple(range(105, 130))

# Inherited Paper 4 calibrated weights (NOT re-fit per cell).
SCORER_WEIGHTS = ScorerWeights(alpha=0.7, beta=0.5, gamma=0.1, delta=0.2)
HRS_WEIGHTS = HRSWeights(patch_posture=0.5, ad_exposure=0.3, telemetry_freshness=0.2)


def _initial_state(seed: int) -> FleetState:
    tables = EEHDAFleetGenerator(seed=seed).generate_all()
    return FleetState(
        vulnerability_records=tables["vulnerability_records"],
        computers=tables["computers"],
        users=tables["users"],
        groups=tables["groups"],
        group_membership_events=tables["group_membership_events"],
        endpoint_patch_state=tables["endpoint_patch_state"],
        telemetry_freshness_log=tables["telemetry_freshness_log"],
    )


def _compute_hrs(state: FleetState) -> pd.Series:
    return HygieneRiskScore(weights=HRS_WEIGHTS).compute(
        endpoint_patch_state=state.endpoint_patch_state,
        vulnerability_records=state.vulnerability_records,
        users=state.users,
        groups=state.groups,
        group_membership_events=state.group_membership_events,
        computers=state.computers,
        telemetry_freshness_log=state.telemetry_freshness_log,
    )


def _label_pairs(pairs: pd.DataFrame, hrs: pd.Series) -> pd.Series:
    if len(pairs) == 0:
        return pd.Series([], dtype=int)
    threshold = hrs.quantile(HRS_PERCENTILE / 100.0)
    host_hrs = pairs["computer_id"].map(hrs)
    return ((pairs["epss_score"] > EPSS_THRESHOLD) & (host_hrs > threshold)).astype(int)


def _score_all(pairs: pd.DataFrame, hrs: pd.Series, seed: int, window: int) -> dict:
    pairs_labeled = pairs.copy()
    pairs_labeled["_label"] = _label_pairs(pairs_labeled, hrs)

    return {
        "HygienePrio-full": HygienePrioScorer(weights=SCORER_WEIGHTS).rank_pairs(pairs_labeled, hrs),
        "EPSS-only": EPSSOnlyScorer().rank_pairs(pairs_labeled),
        "CVSS-only": CVSSOnlyScorer().rank_pairs(pairs_labeled),
        "HRS-only": HRSOnlyScorer().rank_pairs(pairs_labeled, hrs),
        "Random": RandomScorer().rank_pairs(pairs_labeled, seed=seed * 100 + window),
    }


def _advance_cell(
    state: FleetState,
    selected_pairs: pd.DataFrame,
    *,
    window_index: int,
    seed: int,
    lambda_rate: float,
) -> None:
    """Cell-parameterised advance: capacity K is implicit in selected_pairs.

    We re-implement the body of paper5.window_sim.advance_window here so we
    can vary `lambda_rate` independently of paper5's protocol constant.
    """
    rng = np.random.default_rng((seed, window_index, 0))
    acted = apply_remediation(state, selected_pairs)
    disclose_new_cves(state, rng, window_index, rate=lambda_rate)
    update_epss(state, rng)
    update_telemetry_freshness(state, acted)


def _row(
    *, cell_K: int, cell_lambda: float, seed: int, window: int, method: str,
    n_pairs: int, n_pos: int, labels: list,
) -> dict:
    row = {
        "cell_K": cell_K,
        "cell_lambda": cell_lambda,
        "seed": seed,
        "window": window,
        "method": method,
        "n_pairs": n_pairs,
        "n_positives": n_pos,
    }
    for k in METRIC_KS:
        row[f"p_at_{k}"] = round(precision_at_k(labels, k), 4)
    return row


def simulate_cell_seed(cell_K: int, cell_lambda: float, seed: int) -> list[dict]:
    state = _initial_state(seed)
    rows: list[dict] = []
    for w in range(1, N_WINDOWS + 1):
        pairs = applicable_pairs(state)
        hrs = _compute_hrs(state)
        ranked_by_method = _score_all(pairs, hrs, seed, w)

        for method, ranked in ranked_by_method.items():
            labels = ranked["_label"].tolist()
            rows.append(_row(
                cell_K=cell_K, cell_lambda=cell_lambda, seed=seed, window=w,
                method=method, n_pairs=len(pairs), n_pos=int(sum(labels)),
                labels=labels,
            ))

        if w < N_WINDOWS:
            hp_top = ranked_by_method["HygienePrio-full"].head(cell_K)
            _advance_cell(
                state, hp_top,
                window_index=w, seed=seed, lambda_rate=cell_lambda,
            )
    return rows


def run_sweep(
    capacity_grid: Iterable[int] = CAPACITY_GRID,
    lambda_grid: Iterable[float] = LAMBDA_GRID,
    seeds: Optional[Iterable[int]] = None,
    output_dir: Optional[Path] = None,
) -> pd.DataFrame:
    seeds = list(seeds) if seeds is not None else list(EVALUATION_SEEDS)
    cells = [(K, lam) for K in capacity_grid for lam in lambda_grid]
    print(f"Sweep: {len(cells)} cells x {len(seeds)} seeds x {N_WINDOWS} windows")

    rows: list[dict] = []
    for i, (K, lam) in enumerate(cells, 1):
        print(f"[{i}/{len(cells)}] K={K} lambda={lam}", flush=True)
        for s in seeds:
            rows.extend(simulate_cell_seed(K, lam, s))

    df = pd.DataFrame(rows)

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / "sweep_results.csv"
        df.to_csv(out, index=False)
        with open(output_dir / "run_manifest.json", "w") as f:
            json.dump({
                "capacity_grid": list(capacity_grid),
                "lambda_grid": list(lambda_grid),
                "n_windows": N_WINDOWS,
                "metric_ks": list(METRIC_KS),
                "epss_threshold": EPSS_THRESHOLD,
                "hrs_percentile": HRS_PERCENTILE,
                "evaluation_seeds": list(seeds),
                "scorer_weights": SCORER_WEIGHTS.__dict__,
                "hrs_weights": HRS_WEIGHTS.__dict__,
                "n_rows": len(df),
            }, f, indent=2, default=float)
        print(f"Wrote {len(df)} rows to {out}")

    return df
