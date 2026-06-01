"""
Evaluation metrics for HygienePrio.

- Precision@K (P@K)
- NDCG@K
- Oracle-gap (%)
- BCa bootstrap confidence intervals (10,000 resamples)
"""

from __future__ import annotations

import math
from typing import Sequence, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------

def precision_at_k(ranked_labels: Sequence[int], k: int) -> float:
    """
    P@K = |relevant in top-K| / K.

    Parameters
    ----------
    ranked_labels : sequence of 0/1
        Relevance labels in rank order (index 0 = top rank).
    k : int
        Cutoff.
    """
    if k <= 0:
        return 0.0
    top_k = list(ranked_labels)[:k]
    return sum(top_k) / k


def ndcg_at_k(ranked_labels: Sequence[int], k: int) -> float:
    """
    NDCG@K = DCG@K / IDCG@K.

    Binary relevance (0/1). IDCG computed from the same label set.
    """
    if k <= 0:
        return 0.0

    labels = list(ranked_labels)
    actual = labels[:k]
    n_relevant = sum(labels)

    def dcg(rel_list: list[int], cutoff: int) -> float:
        return sum(
            rel / math.log2(i + 2)
            for i, rel in enumerate(rel_list[:cutoff])
        )

    # Ideal: sort all labels descending, take top k
    ideal = sorted(labels, reverse=True)
    idcg = dcg(ideal, k)
    if idcg == 0.0:
        return 0.0
    return dcg(actual, k) / idcg


def oracle_precision_at_k(labels: Sequence[int], k: int) -> float:
    """
    P@K for an oracle that places all true positives first.
    = min(n_relevant, K) / K.
    """
    if k <= 0:
        return 0.0
    n_relevant = sum(labels)
    return min(n_relevant, k) / k


def oracle_gap(ranked_labels: Sequence[int], k: int) -> float:
    """
    Oracle-gap (%) = (P@K_oracle - P@K_method) / P@K_oracle * 100.

    Returns 0.0 if oracle P@K == 0.
    """
    p_oracle = oracle_precision_at_k(ranked_labels, k)
    if p_oracle == 0.0:
        return 0.0
    p_method = precision_at_k(ranked_labels, k)
    return (p_oracle - p_method) / p_oracle * 100.0


# ---------------------------------------------------------------------------
# Bootstrap confidence intervals (BCa)
# ---------------------------------------------------------------------------

def _bca_ci(
    values: np.ndarray,
    stat_fn,
    n_boot: int = 10_000,
    ci: float = 0.95,
    rng: np.random.Generator = None,
) -> Tuple[float, float]:
    """
    BCa (bias-corrected and accelerated) bootstrap CI.

    Parameters
    ----------
    values : array of scalar metric observations (one per seed).
    stat_fn : callable(array) → scalar, e.g. np.mean.
    n_boot : number of bootstrap resamples.
    ci : confidence level.
    rng : numpy Generator for reproducibility.
    """
    if rng is None:
        rng = np.random.default_rng(0)

    n = len(values)
    obs_stat = stat_fn(values)

    # --- Bootstrap resamples ---
    boot_stats = np.array([
        stat_fn(rng.choice(values, size=n, replace=True))
        for _ in range(n_boot)
    ])

    # --- Bias correction (z0) ---
    prop_less = np.mean(boot_stats < obs_stat)
    if prop_less == 0.0 or prop_less == 1.0:
        # Degenerate: fall back to percentile CI
        alpha = (1 - ci) / 2
        return (float(np.percentile(boot_stats, alpha * 100)),
                float(np.percentile(boot_stats, (1 - alpha) * 100)))

    from scipy import stats as scipy_stats
    z0 = scipy_stats.norm.ppf(prop_less)

    # --- Acceleration (a) via jackknife ---
    jack_stats = np.array([
        stat_fn(np.delete(values, i)) for i in range(n)
    ])
    jack_mean = np.mean(jack_stats)
    num = np.sum((jack_mean - jack_stats) ** 3)
    den = 6 * (np.sum((jack_mean - jack_stats) ** 2) ** 1.5)
    a = num / den if den != 0 else 0.0

    # --- Adjusted quantiles ---
    alpha = (1 - ci) / 2
    z_alpha = scipy_stats.norm.ppf(alpha)
    z_1ma = scipy_stats.norm.ppf(1 - alpha)

    def adj_pct(z_in: float) -> float:
        numer = z0 + z_in
        denom = 1.0 - a * (z0 + z_in)
        adj_z = z0 + numer / denom if denom != 0 else z0
        return float(scipy_stats.norm.cdf(adj_z) * 100)

    lo = np.percentile(boot_stats, adj_pct(z_alpha))
    hi = np.percentile(boot_stats, adj_pct(z_1ma))
    return float(lo), float(hi)


def bca_ci_mean(
    per_seed_values: Sequence[float],
    n_boot: int = 10_000,
    ci: float = 0.95,
    seed: int = 0,
) -> Tuple[float, float, float]:
    """
    Compute mean and BCa CI for a collection of per-seed metric values.

    Returns (mean, ci_lower, ci_upper).
    """
    arr = np.array(per_seed_values, dtype=float)
    rng = np.random.default_rng(seed)
    lo, hi = _bca_ci(arr, np.mean, n_boot=n_boot, ci=ci, rng=rng)
    return float(np.mean(arr)), lo, hi
