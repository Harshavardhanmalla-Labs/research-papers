"""
Metrics + ground-truth labellers for Paper 11 (CAP-G).

Re-uses Paper-4 precision_at_k / ndcg_at_k / oracle_gap / bca_ci_mean verbatim and
adds the mission-weighted ground truth (MCTP) and the Criticality-Weighted Exposure
Reduction (CWER) metric (PAPER11_PROTOCOL.md §6).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
_P4 = Path(__file__).resolve().parents[1]  # vendored hygieneprio in local src
if str(_P4) not in sys.path:
    sys.path.insert(0, str(_P4))

from hygieneprio.metrics import (  # noqa: E402  (re-used verbatim)
    precision_at_k,
    ndcg_at_k,
    oracle_gap,
    bca_ci_mean,
)

EPSS_THRESHOLD = 0.10
CONTEXT_PERCENTILE = 75
HRS_PERCENTILE = 75
HIGH_EPSS_EXPOSURE = 0.10  # CWER counts pairs whose CVE clears the exploit gate


# ---------------------------------------------------------------------------
# Ground-truth labellers
# ---------------------------------------------------------------------------

def mctp_labels(
    pairs: pd.DataFrame,
    acs: pd.Series,
    *,
    epss_col: str = "epss_score",
    host_col: str = "computer_id",
) -> pd.Series:
    """
    Mission-Critical True Positive (primary ground truth, §6.1):
        EPSS(c) > 0.10  AND  ACS(h) > fleet 75th percentile.

    ACS is the PRIMARY weighted score, fixed across all methods (no circularity:
    every ranker is scored against the same target).
    """
    acs_threshold = acs.quantile(CONTEXT_PERCENTILE / 100.0)
    host_acs = pairs[host_col].map(acs)
    return (
        (pairs[epss_col] > EPSS_THRESHOLD) & (host_acs > acs_threshold)
    ).astype(int)


def blind_labels(
    pairs: pd.DataFrame,
    hrs: pd.Series,
    *,
    epss_col: str = "epss_score",
    host_col: str = "computer_id",
) -> pd.Series:
    """
    Context-blind ground truth (HygienePrio target, Paper 4 §4.1):
        EPSS(c) > 0.10  AND  HRS(h) > fleet 75th percentile.
    Used to quantify the H4 tradeoff (§6.2).
    """
    hrs_threshold = hrs.quantile(HRS_PERCENTILE / 100.0)
    host_hrs = pairs[host_col].map(hrs)
    return (
        (pairs[epss_col] > EPSS_THRESHOLD) & (host_hrs > hrs_threshold)
    ).astype(int)


# ---------------------------------------------------------------------------
# CWER, Criticality-Weighted Exposure Reduction (§6.2)
# ---------------------------------------------------------------------------

def cwer_at_k(
    ranked: pd.DataFrame,
    acs: pd.Series,
    k: int,
    *,
    epss_col: str = "epss_score",
    host_col: str = "computer_id",
) -> float:
    """
    CWER@K = Σ_{top-K} ACS(h)·1[EPSS(c) > 0.10]   /   oracle top-K sum.

    The oracle sum is the largest achievable top-K total of ACS·1[EPSS>gate] over
    the same pair universe (sort all gate-passing pairs by ACS desc, take K).
    Returns a fraction in [0, 1]; 0 if no pair clears the exploit gate.
    """
    if k <= 0:
        return 0.0

    gate = (ranked[epss_col] > HIGH_EPSS_EXPOSURE).to_numpy()
    host_acs = ranked[host_col].map(acs).fillna(0.0).to_numpy()
    contrib = host_acs * gate  # ACS where CVE clears the gate, else 0

    method_sum = float(contrib[:k].sum())

    # Oracle: best achievable top-K sum of gate-passing ACS contributions.
    oracle_sorted = np.sort(contrib[contrib > 0])[::-1]
    oracle_sum = float(oracle_sorted[:k].sum())
    if oracle_sum <= 0.0:
        return 0.0
    return method_sum / oracle_sum


def ranked_labels(ranked: pd.DataFrame, label_col: str) -> list[int]:
    """Read the (pre-attached) label column in rank order."""
    return ranked[label_col].tolist()


__all__ = [
    "precision_at_k",
    "ndcg_at_k",
    "oracle_gap",
    "bca_ci_mean",
    "mctp_labels",
    "blind_labels",
    "cwer_at_k",
    "ranked_labels",
    "EPSS_THRESHOLD",
    "CONTEXT_PERCENTILE",
    "HRS_PERCENTILE",
]
