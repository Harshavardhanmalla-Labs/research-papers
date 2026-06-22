"""
CAP-G evaluation runner (Paper 11).

For each seed: build a government fleet (EEHDA + context layer, real-corpus EPSS),
fix the mission-weighted (MCTP) and context-blind ground truths, rank with every
method, and compute MWP@K / P@K_blind / CWER@K / NDCG@K (PAPER11_PROTOCOL.md §6-7).

Ground-truth labels are fixed across methods (no circularity): every ranker is
scored against the same MCTP target derived from the PRIMARY weighted ACS.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
_P4 = Path(__file__).resolve().parents[1]  # vendored hygieneprio in local src
if str(_P4) not in sys.path:
    sys.path.insert(0, str(_P4))

from hygieneprio.generator import EEHDAFleetGenerator  # noqa: E402
from hygieneprio.hrs import HygieneRiskScore, HRSWeights  # noqa: E402

from .context import assign_context, asset_context_score, ContextWeights  # noqa: E402
from .scorer import (  # noqa: E402
    CAPGScorer,
    ContextOnlyScorer,
    HygienePrioScorer,
    HYGIENEPRIO_WEIGHTS,
    EPSSOnlyScorer,
    CVSSOnlyScorer,
    HRSOnlyScorer,
    RandomScorer,
)
from .metrics import (  # noqa: E402
    mctp_labels,
    blind_labels,
    precision_at_k,
    ndcg_at_k,
    cwer_at_k,
)

# Pre-registered constants (PAPER11_PROTOCOL.md §6, §9).
K_VALUES = [50, 100, 250]
EVALUATION_SEEDS = list(range(200, 225))          # 25 seeds (§9)
CALIBRATION_SEEDS = [11, 22, 33, 44, 55]          # held out (§5.3)
RHO_GRID = [0.5, 1.0, 2.0, 4.0, 8.0]              # calibration grid (§5.3)
HRS_WEIGHTS = HRSWeights(patch_posture=0.5, ad_exposure=0.3, telemetry_freshness=0.2)
REAL_CORPUS = Path(__file__).resolve().parents[2] / "data" / "cve_corpus_for_sampling.csv"  # vendored

# Context-ablation configs for the CAP-G scorer (§7). MCTP target stays primary.
_CONTEXT_ABLATIONS = {
    "CAP-G-full":   ("weighted", ContextWeights(0.5, 0.3, 0.2)),
    "CAP-G-noCrit": ("weighted", ContextWeights(0.0, 0.3, 0.2)),
    "CAP-G-noZone": ("weighted", ContextWeights(0.5, 0.0, 0.2)),
    "CAP-G-noSens": ("weighted", ContextWeights(0.5, 0.3, 0.0)),
    "CAP-G-hwm":    ("hwm",      ContextWeights(0.5, 0.3, 0.2)),
}


def _resample_real_epss(vr: pd.DataFrame, corpus: pd.DataFrame,
                        rng: np.random.Generator) -> pd.DataFrame:
    """Replace synthetic EPSS/KEV with values resampled from the real corpus
    (Paper-10 procedure), preserving fleet structure and patch state."""
    vr = vr.copy()
    n = len(vr)
    idx = rng.integers(0, len(corpus), n)
    sampled = corpus.iloc[idx][["epss", "in_kev"]].reset_index(drop=True)
    vr["epss_score"] = np.clip(sampled["epss"].to_numpy(dtype=float), 1e-4, 1.0)
    vr["in_kev"] = sampled["in_kev"].to_numpy()
    vr["days_since_kev_entry"] = np.where(
        vr["in_kev"].to_numpy(), rng.integers(0, 30, size=n).astype(float), np.nan
    )
    return vr


def build_fleet(seed: int, corpus: pd.DataFrame, *, homogeneous: bool = False):
    """Construct one government-fleet seed. Returns (pairs_labeled, hrs, acs_primary,
    computers_ctx)."""
    tables = EEHDAFleetGenerator(seed=seed).generate_all()
    rng = np.random.default_rng((seed, 7))  # EPSS-resampling stream
    pairs = _resample_real_epss(tables["vulnerability_records"], corpus, rng)
    pairs = pairs.reset_index(drop=True)

    computers_ctx = assign_context(tables["computers"], seed, homogeneous=homogeneous)

    hrs = HygieneRiskScore(weights=HRS_WEIGHTS).compute(
        endpoint_patch_state=tables["endpoint_patch_state"],
        vulnerability_records=pairs,
        users=tables["users"],
        groups=tables["groups"],
        group_membership_events=tables["group_membership_events"],
        computers=computers_ctx,
        telemetry_freshness_log=tables["telemetry_freshness_log"],
    )

    # PRIMARY weighted ACS, defines the MCTP target, fixed across all methods.
    acs_primary = asset_context_score(
        computers_ctx, ContextWeights(0.5, 0.3, 0.2), aggregation="weighted"
    )

    # Fixed ground-truth label columns.
    pairs["_mctp"] = mctp_labels(pairs, acs_primary).to_numpy()
    pairs["_blind"] = blind_labels(pairs, hrs).to_numpy()
    return pairs, hrs, acs_primary, computers_ctx


def _metric_row(ranked: pd.DataFrame, acs_primary: pd.Series, *,
                method: str, seed: int, fleet_type: str,
                n_pairs: int, n_mctp: int, n_blind: int) -> dict:
    mctp = ranked["_mctp"].tolist()
    blind = ranked["_blind"].tolist()
    row = {
        "seed": seed, "method": method, "fleet_type": fleet_type,
        "n_pairs": n_pairs, "n_mctp": n_mctp, "n_blind": n_blind,
    }
    for k in K_VALUES:
        row[f"mwp_at_{k}"]    = round(precision_at_k(mctp, k), 4)
        row[f"pblind_at_{k}"] = round(precision_at_k(blind, k), 4)
        row[f"ndcg_at_{k}"]   = round(ndcg_at_k(mctp, k), 4)
        row[f"cwer_at_{k}"]   = round(cwer_at_k(ranked, acs_primary, k), 4)
    return row


def evaluate_seed(seed: int, corpus: pd.DataFrame, rho: float, *,
                  homogeneous: bool = False) -> list[dict]:
    """Run all methods on one seed. Returns list of metric-row dicts."""
    pairs, hrs, acs_primary, computers_ctx = build_fleet(
        seed, corpus, homogeneous=homogeneous
    )
    n_pairs = len(pairs)
    n_mctp = int(pairs["_mctp"].sum())
    n_blind = int(pairs["_blind"].sum())
    fleet_type = "homogeneous" if homogeneous else "heterogeneous"

    def mk(ranked, method):
        return _metric_row(ranked, acs_primary, method=method, seed=seed,
                           fleet_type=fleet_type, n_pairs=n_pairs,
                           n_mctp=n_mctp, n_blind=n_blind)

    rows: list[dict] = []

    # --- Simple baselines ---
    rows.append(mk(EPSSOnlyScorer().rank_pairs(pairs), "EPSS-only"))
    rows.append(mk(CVSSOnlyScorer().rank_pairs(pairs), "CVSS-only"))
    rows.append(mk(RandomScorer().rank_pairs(pairs, seed=seed), "Random"))
    rows.append(mk(HRSOnlyScorer().rank_pairs(pairs, hrs), "HRS-only"))
    rows.append(mk(ContextOnlyScorer().rank_pairs(pairs, acs_primary), "Context-only"))

    # --- HygienePrio (context-blind primary comparison) ---
    rows.append(mk(HygienePrioScorer(weights=HYGIENEPRIO_WEIGHTS).rank_pairs(pairs, hrs),
                   "HygienePrio"))

    # --- CAP-G variants (each uses its own ACS aggregation; MCTP target fixed) ---
    capg = CAPGScorer(rho=rho)
    for method, (agg, cw) in _CONTEXT_ABLATIONS.items():
        acs_variant = asset_context_score(computers_ctx, cw, aggregation=agg)
        rows.append(mk(capg.rank_pairs(pairs, hrs, acs_variant), method))

    return rows


def calibrate_rho(corpus: pd.DataFrame) -> dict:
    """Grid-search rho on held-out calibration seeds; objective = mean MWP@50 of
    CAP-G-full. Returns the calibration record (PAPER11_PROTOCOL.md §5.3)."""
    record = {"grid": RHO_GRID, "objective": "mean MWP@50 (CAP-G-full)",
              "calibration_seeds": CALIBRATION_SEEDS, "per_rho": {}}
    best_rho, best_obj = RHO_GRID[0], -1.0
    # HygienePrio reference on calibration seeds (for the §8 calibration stop rule).
    hp_mwp50 = []
    for rho in RHO_GRID:
        mwp50 = []
        for seed in CALIBRATION_SEEDS:
            pairs, hrs, acs_primary, computers_ctx = build_fleet(seed, corpus)
            acs_full = asset_context_score(computers_ctx, ContextWeights(0.5, 0.3, 0.2))
            ranked = CAPGScorer(rho=rho).rank_pairs(pairs, hrs, acs_full)
            mwp50.append(precision_at_k(ranked["_mctp"].tolist(), 50))
            if rho == RHO_GRID[0]:
                hp = HygienePrioScorer(weights=HYGIENEPRIO_WEIGHTS).rank_pairs(pairs, hrs)
                hp_mwp50.append(precision_at_k(hp["_mctp"].tolist(), 50))
        obj = float(np.mean(mwp50))
        record["per_rho"][str(rho)] = round(obj, 4)
        if obj > best_obj:
            best_obj, best_rho = obj, rho
    record["selected_rho"] = best_rho
    record["selected_mwp50"] = round(best_obj, 4)
    record["hygieneprio_mwp50"] = round(float(np.mean(hp_mwp50)), 4)
    record["calibration_gain_pp"] = round((best_obj - float(np.mean(hp_mwp50))) * 100, 2)
    return record


def run_evaluation(rho: float, corpus: pd.DataFrame,
                   seeds: Optional[list[int]] = None) -> pd.DataFrame:
    """Run the primary heterogeneous-fleet evaluation across seeds."""
    seeds = seeds or EVALUATION_SEEDS
    all_rows = []
    for seed in seeds:
        print(f"  [het] seed {seed}...", end=" ", flush=True)
        all_rows.extend(evaluate_seed(seed, corpus, rho, homogeneous=False))
        print("done")
    return pd.DataFrame(all_rows)


def run_homogeneous_control(rho: float, corpus: pd.DataFrame,
                            seeds: Optional[list[int]] = None) -> pd.DataFrame:
    """Run the H3 mechanism control (homogeneous fleet) for HygienePrio + CAP-G-full."""
    seeds = seeds or EVALUATION_SEEDS
    all_rows = []
    for seed in seeds:
        print(f"  [hom] seed {seed}...", end=" ", flush=True)
        rows = evaluate_seed(seed, corpus, rho, homogeneous=True)
        all_rows.extend(r for r in rows if r["method"] in ("HygienePrio", "CAP-G-full"))
        print("done")
    return pd.DataFrame(all_rows)
