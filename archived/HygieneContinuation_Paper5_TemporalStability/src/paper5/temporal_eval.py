"""Multi-window evaluation runner for Paper 5.

For each seed and each window:
  1. Recompute HRS from the current fleet state.
  2. Re-label pairs (per-window ground truth using current HRS 75th percentile).
  3. Score and rank with each of the 5 methods.
  4. Compute P@K for K ∈ {50, 100, 250}.
  5. Append one row per (seed, window, method, K) to the frozen results CSV.

The remediation policy that drives fleet evolution is fixed to
HygienePrio-full's top-50 selection at each window — see PAPER5_PROTOCOL.md
§5.3 and the threats section of the manuscript (§9, internal validity).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Locate paper4's source so its hygieneprio package is importable.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_PAPER4_SRC = _REPO_ROOT / "paper4" / "src"
if str(_PAPER4_SRC) not in sys.path:
    sys.path.insert(0, str(_PAPER4_SRC))

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

from .window_sim import (
    FleetState,
    advance_window,
    applicable_pairs,
)


# ---------------------------------------------------------------------------
# Pre-registered constants (PAPER5_PROTOCOL.md)
# ---------------------------------------------------------------------------

N_WINDOWS = 6
K_VALUES = (50, 100, 250)
SELECTION_K = 50            # capacity used to drive fleet evolution
EPSS_THRESHOLD = 0.10       # ground truth condition 1 (same as paper4)
HRS_PERCENTILE = 75         # ground truth condition 2; recomputed each window

CALIBRATION_SEEDS = tuple(range(100, 105))    # 100..104
EVALUATION_SEEDS = tuple(range(105, 130))     # 105..129  (25 seeds)

# Calibrated weights inherited from paper4 (NOT re-calibrated between windows).
SCORER_WEIGHTS = ScorerWeights(alpha=0.7, beta=0.5, gamma=0.1, delta=0.2)
HRS_WEIGHTS = HRSWeights(patch_posture=0.5, ad_exposure=0.3, telemetry_freshness=0.2)


# ---------------------------------------------------------------------------
# Per-seed simulation
# ---------------------------------------------------------------------------

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


def _compute_hrs(state: FleetState, weights: HRSWeights = HRS_WEIGHTS) -> pd.Series:
    return HygieneRiskScore(weights=weights).compute(
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


def _score_all_methods(
    pairs: pd.DataFrame,
    hrs: pd.Series,
    seed: int,
    window: int,
) -> dict[str, pd.DataFrame]:
    """Return a dict {method_name: ranked DataFrame with '_label' column}."""
    pairs_labeled = pairs.copy()
    pairs_labeled["_label"] = _label_pairs(pairs_labeled, hrs)

    hp = HygienePrioScorer(weights=SCORER_WEIGHTS)
    hp_ranked = hp.rank_pairs(pairs_labeled, hrs)

    epss_ranked = EPSSOnlyScorer().rank_pairs(pairs_labeled)
    cvss_ranked = CVSSOnlyScorer().rank_pairs(pairs_labeled)
    hrs_ranked = HRSOnlyScorer().rank_pairs(pairs_labeled, hrs)
    # Deterministic per-(seed, window) RNG so the Random baseline is reproducible.
    rand_ranked = RandomScorer().rank_pairs(pairs_labeled, seed=seed * 100 + window)

    return {
        "HygienePrio-full": hp_ranked,
        "EPSS-only": epss_ranked,
        "CVSS-only": cvss_ranked,
        "HRS-only": hrs_ranked,
        "Random": rand_ranked,
    }


def _row(seed: int, window: int, method: str, n_pairs: int, n_pos: int,
         ranked_labels: list[int]) -> dict:
    row = {
        "seed": seed,
        "window": window,
        "method": method,
        "n_pairs": n_pairs,
        "n_positives": n_pos,
    }
    for k in K_VALUES:
        row[f"p_at_{k}"] = round(precision_at_k(ranked_labels, k), 4)
    return row


def simulate_seed(seed: int) -> list[dict]:
    """Run all W windows for one seed across all 5 methods."""
    state = _initial_state(seed)
    rows: list[dict] = []

    for w in range(1, N_WINDOWS + 1):
        pairs = applicable_pairs(state)
        hrs = _compute_hrs(state)

        ranked_by_method = _score_all_methods(pairs, hrs, seed, w)

        # Record metrics for all methods at this window.
        for method, ranked in ranked_by_method.items():
            labels = ranked["_label"].tolist()
            n_pos = int(sum(labels))
            rows.append(_row(seed, w, method, len(pairs), n_pos, labels))

        # Advance fleet using HygienePrio-full's top-K (selection policy).
        if w < N_WINDOWS:
            hp_top = ranked_by_method["HygienePrio-full"].head(SELECTION_K)
            advance_window(state, hp_top, window_index=w, seed=seed)

    return rows


# ---------------------------------------------------------------------------
# Top-level runner
# ---------------------------------------------------------------------------

def run_temporal_evaluation(
    seeds: Optional[list[int]] = None,
    output_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """Run the multi-window evaluation and (optionally) persist results."""
    if seeds is None:
        seeds = list(EVALUATION_SEEDS)

    all_rows: list[dict] = []
    for s in seeds:
        print(f"  seed {s}...", end=" ", flush=True)
        all_rows.extend(simulate_seed(s))
        print("done")

    df = pd.DataFrame(all_rows)

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        results_path = output_dir / "temporal_results.csv"
        df.to_csv(results_path, index=False)
        manifest = {
            "n_windows": N_WINDOWS,
            "k_values": list(K_VALUES),
            "selection_k": SELECTION_K,
            "epss_threshold": EPSS_THRESHOLD,
            "hrs_percentile": HRS_PERCENTILE,
            "calibration_seeds": list(CALIBRATION_SEEDS),
            "evaluation_seeds": list(EVALUATION_SEEDS),
            "scorer_weights": SCORER_WEIGHTS.__dict__,
            "hrs_weights": HRS_WEIGHTS.__dict__,
        }
        with open(output_dir / "run_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2, default=float)
        print(f"Wrote {len(df)} rows to {results_path}")

    return df
