"""
HygienePrio evaluation runner.

Runs all nine methods across evaluation seeds, computes P@K / NDCG@K / Oracle-gap,
and writes primary_results.csv.

Ground truth (pre-registered, PAPER4_PROTOCOL.md §4):
  True positive (h, c) if:
    EPSS(c) > 0.10  AND
    HRS(h) > fleet 75th percentile  AND
    (h, c) ∈ V  (applicable CVE-host pair)

Note: The HRS condition creates a structural advantage for HygienePrio-full and
HRS-containing ablation variants. Acknowledged as a threat to validity in §9.1.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .generator import EEHDAFleetGenerator
from .hrs import HygieneRiskScore, HRSWeights
from .scorer import (
    HygienePrioScorer,
    ScorerWeights,
    EPSSOnlyScorer,
    CVSSOnlyScorer,
    HRSOnlyScorer,
    RandomScorer,
)
from .metrics import precision_at_k, ndcg_at_k, oracle_gap

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

K_VALUES = [50, 100, 250]
EPSS_THRESHOLD = 0.10      # Ground truth condition 1
HRS_PERCENTILE = 75        # Ground truth condition 2

# Pre-registered calibrated weights (grid search on 5 calibration seeds)
CALIBRATED_WEIGHTS = ScorerWeights(alpha=0.7, beta=0.5, gamma=0.1, delta=0.2)

# Pre-registered HRS dimension weights
HRS_WEIGHTS = HRSWeights(patch_posture=0.5, ad_exposure=0.3, telemetry_freshness=0.2)

# Calibration seeds (fixed before evaluation; NOT used in primary results)
CALIBRATION_SEEDS = [11, 22, 33, 44, 55]

# Evaluation seeds (25 seeds; primary results)
EVALUATION_SEEDS = list(range(100, 125))  # seeds 100-124 inclusive


# ---------------------------------------------------------------------------
# Ablation weight configurations
# ---------------------------------------------------------------------------

def _make_ablation_weights() -> dict[str, tuple[ScorerWeights, HRSWeights]]:
    """
    Ablation configs: zero out one HRS dimension WITHOUT renormalizing.

    This preserves the relative weighting of remaining dimensions and prevents
    the artifact where removing a weak dimension amplifies a stronger one.
    Unnormalized HRS sums to < 1.0 but this is handled consistently since
    β in the scorer is applied uniformly to the HRS output.
    """
    return {
        "HygienePrio-full": (
            CALIBRATED_WEIGHTS,
            HRS_WEIGHTS,                       # w=(0.5, 0.3, 0.2) sum=1.0
        ),
        "HygienePrio-noInteraction": (
            ScorerWeights(alpha=0.7, beta=0.5, gamma=0.1, delta=0.0),
            HRS_WEIGHTS,                       # same HRS, no interaction term
        ),
        "HygienePrio-noPatch": (
            CALIBRATED_WEIGHTS,
            HRSWeights(patch_posture=0.0, ad_exposure=0.3, telemetry_freshness=0.2),  # sum=0.5
        ),
        "HygienePrio-noAD": (
            CALIBRATED_WEIGHTS,
            HRSWeights(patch_posture=0.5, ad_exposure=0.0, telemetry_freshness=0.2),  # sum=0.7
        ),
        "HygienePrio-noFreshness": (
            CALIBRATED_WEIGHTS,
            HRSWeights(patch_posture=0.5, ad_exposure=0.3, telemetry_freshness=0.0),  # sum=0.8
        ),
    }


# ---------------------------------------------------------------------------
# Ground truth labelling
# ---------------------------------------------------------------------------

def label_pairs(
    pairs: pd.DataFrame,
    hrs: pd.Series,
    *,
    epss_col: str = "epss_score",
    host_col: str = "computer_id",
) -> pd.Series:
    """
    Assign binary true-positive labels to each (host, CVE) pair.

    Pre-registered definition (§3.2):
      label = 1 if EPSS(c) > 0.10 AND HRS(h) > 75th percentile.
    """
    hrs_threshold = hrs.quantile(HRS_PERCENTILE / 100.0)
    host_hrs = pairs[host_col].map(hrs)
    labels = (
        (pairs[epss_col] > EPSS_THRESHOLD) &
        (host_hrs > hrs_threshold)
    ).astype(int)
    return labels


# ---------------------------------------------------------------------------
# Single-seed evaluation
# ---------------------------------------------------------------------------

def _hash_ranked_list(ranked: pd.DataFrame) -> str:
    """Content-address the ranked list for integrity verification."""
    cols = [c for c in ["computer_id", "cve_id", "score", "epss_score"] if c in ranked.columns]
    return hashlib.sha256(ranked[cols].to_csv(index=False).encode()).hexdigest()[:16]


def _ranked_labels_from(ranked: pd.DataFrame, label_col: str = "_label") -> list[int]:
    """
    Extract the label column from an already-sorted ranked DataFrame.

    The ranked DataFrame retains the original index (pairs are sorted but
    index values identify original rows). Labels were attached to the
    DataFrame BEFORE sorting, so we just read the column in order.
    """
    return ranked[label_col].tolist()


def _attach_labels(pairs: pd.DataFrame, labels: pd.Series) -> pd.DataFrame:
    """Attach a label Series (same index as pairs) as a column '_label'."""
    df = pairs.copy()
    df["_label"] = labels
    return df


def evaluate_seed(seed: int) -> list[dict]:
    """Run all methods for one seed. Returns list of result dicts."""
    tables = EEHDAFleetGenerator(seed=seed).generate_all()
    pairs = tables["vulnerability_records"].reset_index(drop=True)
    computers = tables["computers"]

    hrs_calculator = HygieneRiskScore(weights=HRS_WEIGHTS)
    hrs = hrs_calculator.compute(
        endpoint_patch_state=tables["endpoint_patch_state"],
        vulnerability_records=pairs,
        users=tables["users"],
        groups=tables["groups"],
        group_membership_events=tables["group_membership_events"],
        computers=computers,
        telemetry_freshness_log=tables["telemetry_freshness_log"],
    )

    # Base labels (used for EPSS-only, CVSS-only, HRS-only, Random)
    labels_series = label_pairs(pairs, hrs)
    n_positives = int(labels_series.sum())
    pairs_labeled = _attach_labels(pairs, labels_series)

    results = []
    ablation_configs = _make_ablation_weights()

    # --- HygienePrio variants ---
    # Ground truth labels are FIXED for all methods using the calibrated HRS weights.
    # This prevents circularity inflating ablation-variant performance:
    # each ablation variant is scored against the same set of true positives.
    # (Acknowledged in §8.4: HygienePrio-full still has a structural advantage over
    # baselines that don't use HRS at all, because labels include HRS > P75 condition.)
    for method_name, (sw, hrw) in ablation_configs.items():
        hrs_variant = HygieneRiskScore(weights=hrw)
        hrs_v = hrs_variant.compute(
            endpoint_patch_state=tables["endpoint_patch_state"],
            vulnerability_records=pairs,
            users=tables["users"],
            groups=tables["groups"],
            group_membership_events=tables["group_membership_events"],
            computers=computers,
            telemetry_freshness_log=tables["telemetry_freshness_log"],
        )
        # Score pairs using variant HRS, but evaluate against fixed base labels
        pairs_v = _attach_labels(pairs, labels_series)

        scorer = HygienePrioScorer(weights=sw)
        ranked = scorer.rank_pairs(pairs_v, hrs_v)
        ranked_labels = _ranked_labels_from(ranked)

        row = {
            "seed": seed,
            "method": method_name,
            "n_pairs": len(pairs),
            "n_positives": n_positives,
            "ranked_list_hash": _hash_ranked_list(ranked),
        }
        for k in K_VALUES:
            row[f"p_at_{k}"] = round(precision_at_k(ranked_labels, k), 4)
            row[f"ndcg_at_{k}"] = round(ndcg_at_k(ranked_labels, k), 4)
            row[f"oracle_gap_at_{k}"] = round(oracle_gap(ranked_labels, k), 2)
        results.append(row)

    # --- EPSS-only baseline ---
    epss_scorer = EPSSOnlyScorer()
    epss_ranked = epss_scorer.rank_pairs(pairs_labeled)
    row = {
        "seed": seed, "method": "EPSS-only",
        "n_pairs": len(pairs), "n_positives": n_positives,
        "ranked_list_hash": _hash_ranked_list(epss_ranked),
    }
    for k in K_VALUES:
        epss_labels = _ranked_labels_from(epss_ranked)
        row[f"p_at_{k}"] = round(precision_at_k(epss_labels, k), 4)
        row[f"ndcg_at_{k}"] = round(ndcg_at_k(epss_labels, k), 4)
        row[f"oracle_gap_at_{k}"] = round(oracle_gap(epss_labels, k), 2)
    results.append(row)

    # --- CVSS-only baseline ---
    cvss_scorer = CVSSOnlyScorer()
    cvss_ranked = cvss_scorer.rank_pairs(pairs_labeled)
    cvss_labels = _ranked_labels_from(cvss_ranked)
    row = {
        "seed": seed, "method": "CVSS-only",
        "n_pairs": len(pairs), "n_positives": n_positives,
        "ranked_list_hash": _hash_ranked_list(cvss_ranked),
    }
    for k in K_VALUES:
        row[f"p_at_{k}"] = round(precision_at_k(cvss_labels, k), 4)
        row[f"ndcg_at_{k}"] = round(ndcg_at_k(cvss_labels, k), 4)
        row[f"oracle_gap_at_{k}"] = round(oracle_gap(cvss_labels, k), 2)
    results.append(row)

    # --- HRS-only baseline ---
    hrs_only_scorer = HRSOnlyScorer()
    hrs_ranked = hrs_only_scorer.rank_pairs(pairs_labeled, hrs)
    hrs_labels = _ranked_labels_from(hrs_ranked)
    row = {
        "seed": seed, "method": "HRS-only",
        "n_pairs": len(pairs), "n_positives": n_positives,
        "ranked_list_hash": _hash_ranked_list(hrs_ranked),
    }
    for k in K_VALUES:
        row[f"p_at_{k}"] = round(precision_at_k(hrs_labels, k), 4)
        row[f"ndcg_at_{k}"] = round(ndcg_at_k(hrs_labels, k), 4)
        row[f"oracle_gap_at_{k}"] = round(oracle_gap(hrs_labels, k), 2)
    results.append(row)

    # --- Random baseline ---
    rand_scorer = RandomScorer()
    rand_ranked = rand_scorer.rank_pairs(pairs_labeled, seed=seed)
    rand_labels = _ranked_labels_from(rand_ranked)
    row = {
        "seed": seed, "method": "Random",
        "n_pairs": len(pairs), "n_positives": n_positives,
        "ranked_list_hash": _hash_ranked_list(rand_ranked),
    }
    for k in K_VALUES:
        row[f"p_at_{k}"] = round(precision_at_k(rand_labels, k), 4)
        row[f"ndcg_at_{k}"] = round(ndcg_at_k(rand_labels, k), 4)
        row[f"oracle_gap_at_{k}"] = round(oracle_gap(rand_labels, k), 2)
    results.append(row)

    return results


# ---------------------------------------------------------------------------
# Full evaluation loop
# ---------------------------------------------------------------------------

def run_evaluation(
    seeds: Optional[list[int]] = None,
    output_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Run HygienePrio evaluation across all seeds.

    Parameters
    ----------
    seeds : list of int, optional
        Seeds to evaluate. Defaults to EVALUATION_SEEDS (25 seeds).
    output_dir : Path, optional
        Directory to write primary_results.csv and run_manifest.json.

    Returns
    -------
    pd.DataFrame
        Primary results table (one row per seed × method).
    """
    if seeds is None:
        seeds = EVALUATION_SEEDS

    all_results = []
    for seed in seeds:
        print(f"  seed {seed}...", end=" ", flush=True)
        seed_results = evaluate_seed(seed)
        all_results.extend(seed_results)
        print("done")

    df = pd.DataFrame(all_results)

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        results_path = output_dir / "primary_results.csv"
        df.to_csv(results_path, index=False)
        print(f"Wrote {len(df)} rows to {results_path}")

        manifest = {
            "evaluation_seeds": seeds,
            "calibration_seeds": CALIBRATION_SEEDS,
            "k_values": K_VALUES,
            "epss_threshold": EPSS_THRESHOLD,
            "hrs_percentile": HRS_PERCENTILE,
            "calibrated_weights": {
                "alpha": CALIBRATED_WEIGHTS.alpha,
                "beta": CALIBRATED_WEIGHTS.beta,
                "gamma": CALIBRATED_WEIGHTS.gamma,
                "delta": CALIBRATED_WEIGHTS.delta,
                "kev_decay_lambda": CALIBRATED_WEIGHTS.kev_decay_lambda,
            },
            "hrs_weights": {
                "patch_posture": HRS_WEIGHTS.patch_posture,
                "ad_exposure": HRS_WEIGHTS.ad_exposure,
                "telemetry_freshness": HRS_WEIGHTS.telemetry_freshness,
            },
        }
        with open(output_dir / "run_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

    return df
