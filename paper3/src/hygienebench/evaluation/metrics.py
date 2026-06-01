"""
Evaluation metrics for HygieneBench.

Primary metrics (per EXPERIMENTAL_DESIGN_v0_1.md):
  - Average Precision (AP) — primary ranking metric
  - Precision@k (P@k) — practical operational metric
  - Recall@k (R@k) — coverage at fixed review budget
  - False Positive Burden (FPB) — 1 - P@k, analyst cost proxy
  - Rank Stability (τ) — Kendall's τ across seeds
  - failure_flag() — negative-result protocol (δ=0.05)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import kendalltau
from typing import Dict, List, Optional, Sequence


def _validate_inputs(scores: np.ndarray, labels: np.ndarray) -> None:
    if len(scores) != len(labels):
        raise ValueError(f"scores length {len(scores)} != labels length {len(labels)}")
    if len(scores) == 0:
        raise ValueError("Empty scores/labels")


def precision_at_k(scores: np.ndarray, labels: np.ndarray, k: int) -> float:
    """Fraction of true positives in the top-k highest-scored entities."""
    _validate_inputs(scores, labels)
    k = min(k, len(scores))
    if k == 0:
        return 0.0
    top_k_idx = np.argsort(scores)[::-1][:k]
    return float(np.sum(labels[top_k_idx])) / k


def recall_at_k(scores: np.ndarray, labels: np.ndarray, k: int) -> float:
    """Fraction of all true positives captured in the top-k ranked entities."""
    _validate_inputs(scores, labels)
    k = min(k, len(scores))
    n_pos = int(np.sum(labels))
    if n_pos == 0:
        return 0.0
    top_k_idx = np.argsort(scores)[::-1][:k]
    return float(np.sum(labels[top_k_idx])) / n_pos


def false_positive_burden(scores: np.ndarray, labels: np.ndarray, k: int) -> float:
    """1 - P@k; fraction of analyst review budget wasted on non-anomalies."""
    return 1.0 - precision_at_k(scores, labels, k)


def average_precision(scores: np.ndarray, labels: np.ndarray) -> float:
    """
    Area under the precision-recall curve (sklearn-compatible AP).
    Uses the interpolated trapezoidal definition matching sklearn.metrics.average_precision_score.
    Implemented without sklearn dependency for portability.
    """
    _validate_inputs(scores, labels)
    n_pos = int(np.sum(labels))
    if n_pos == 0:
        return 0.0

    sorted_idx = np.argsort(scores)[::-1]
    sorted_labels = labels[sorted_idx]

    tp = np.cumsum(sorted_labels)
    fp = np.cumsum(1 - sorted_labels)
    precision = tp / (tp + fp)
    recall = tp / n_pos

    # Insert (recall=0, precision=1) sentinel
    precision = np.concatenate([[1.0], precision])
    recall = np.concatenate([[0.0], recall])

    ap = float(np.sum((recall[1:] - recall[:-1]) * precision[1:]))
    return ap


def rank_stability(
    scores_list: List[np.ndarray],
    labels_list: Optional[List[np.ndarray]] = None,
    top_n: int = 50,
) -> float:
    """
    Mean pairwise Kendall's τ across a list of score arrays (one per seed).

    Computed over the union of top-N ranked entities across all seeds,
    restricted to the common entity index. If only one score array is
    provided, returns 1.0 (trivially stable).
    """
    if len(scores_list) < 2:
        return 1.0

    n_pairs = 0
    tau_sum = 0.0

    for i in range(len(scores_list)):
        for j in range(i + 1, len(scores_list)):
            a = scores_list[i]
            b = scores_list[j]
            min_len = min(len(a), len(b))
            if min_len < 2:
                continue
            # Use top_n entities from the first array as the comparison set
            candidate_idx = np.argsort(a[:min_len])[::-1][:top_n]
            tau_val, _ = kendalltau(a[candidate_idx], b[candidate_idx])
            if not np.isnan(tau_val):
                tau_sum += tau_val
                n_pairs += 1

    return float(tau_sum / n_pairs) if n_pairs > 0 else float("nan")


def failure_flag(
    ap_scores: Sequence[float],
    pk_scores: Sequence[float],
    rule_ap: float,
    rule_pk: float,
    delta_ap: float = 0.05,
    delta_pk: float = 0.05,
    min_seed_fraction: float = 2 / 3,
) -> bool:
    """
    Return True when a method fails to beat the rule baseline by δ in ≥2/3 seeds.

    Failure condition (per EXPERIMENTAL_DESIGN_v0_1.md §6):
      delta_AP < 0.05 AND delta_P@k < 0.05 in at least ceil(2/3 * n_seeds) seeds.

    A flagged run is reported as a negative result — not filtered from results.
    """
    ap_scores = list(ap_scores)
    pk_scores = list(pk_scores)
    n_seeds = len(ap_scores)
    if n_seeds == 0:
        return False

    min_failing = int(np.ceil(min_seed_fraction * n_seeds))

    failing = 0
    for ap, pk in zip(ap_scores, pk_scores):
        ap_delta = ap - rule_ap
        pk_delta = pk - rule_pk
        if ap_delta < delta_ap and pk_delta < delta_pk:
            failing += 1

    return failing >= min_failing


def compute_metrics(
    scores: np.ndarray,
    labels: np.ndarray,
    k: int,
    rule_scores: Optional[np.ndarray] = None,
    rule_labels: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """
    Compute the full metric suite for one (method, task, seed, condition) run.

    Returns a dict with keys: ap, pk, rk, fpb.
    If rule_scores provided, also includes rule_ap, rule_pk.
    """
    labels = labels.astype(int)
    result: Dict[str, float] = {
        "ap": average_precision(scores, labels),
        "pk": precision_at_k(scores, labels, k),
        "rk": recall_at_k(scores, labels, k),
        "fpb": false_positive_burden(scores, labels, k),
    }

    if rule_scores is not None and rule_labels is not None:
        rule_labels = rule_labels.astype(int)
        result["rule_ap"] = average_precision(rule_scores, rule_labels)
        result["rule_pk"] = precision_at_k(rule_scores, rule_labels, k)

    return result
