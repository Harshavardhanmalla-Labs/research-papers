"""
HygienePrio scorer.

S(h, c) = α × EPSS(c)
         + β × HRS(h)
         + γ × KEV_recency(c)
         + δ × (EPSS(c) × HRS(h))

All weights are non-negative (monotonicity constraint).
Calibrated weights (from 5 held-out seeds, pre-registered): α=0.7, β=0.5, γ=0.1, δ=0.2
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from typing import Optional


@dataclass
class ScorerWeights:
    """
    HygienePrio scorer weights.

    Calibrated defaults (from grid search on 5 held-out calibration seeds,
    objective = mean P@50; fixed before primary evaluation).
    """
    alpha: float = 0.7   # EPSS exploit likelihood weight
    beta: float = 0.5    # HRS host hygiene weight
    gamma: float = 0.1   # KEV recency weight
    delta: float = 0.2   # EPSS × HRS interaction weight
    kev_decay_lambda: float = 0.05  # KEV_recency decay constant (~14-day half-life)

    def __post_init__(self) -> None:
        for name, val in [
            ("alpha", self.alpha), ("beta", self.beta),
            ("gamma", self.gamma), ("delta", self.delta),
        ]:
            if val < 0:
                raise ValueError(f"Weight '{name}' must be non-negative, got {val}")


class HygienePrioScorer:
    """
    Score each applicable (host, CVE) pair and return a ranked list.

    Parameters
    ----------
    weights : ScorerWeights, optional
        Scorer weights. Uses calibrated defaults if not provided.
    """

    def __init__(self, weights: Optional[ScorerWeights] = None) -> None:
        self.weights = weights or ScorerWeights()

    def kev_recency(self, days_since_kev_entry: float) -> float:
        """
        KEV_recency(c) = exp(−λ × days_since_kev_entry)  if c ∈ KEV
                       = 0                                 otherwise.

        Pass NaN or negative values to indicate non-KEV CVEs.
        """
        if pd.isna(days_since_kev_entry) or days_since_kev_entry < 0:
            return 0.0
        return math.exp(-self.weights.kev_decay_lambda * days_since_kev_entry)

    def score_pairs(
        self,
        pairs: pd.DataFrame,
        hrs: pd.Series,
        *,
        host_col: str = "computer_id",
        cve_col: str = "cve_id",
        epss_col: str = "epss_score",
        kev_days_col: str = "days_since_kev_entry",
    ) -> pd.DataFrame:
        """
        Compute S(h, c) for each (host, CVE) pair in ``pairs``.

        Parameters
        ----------
        pairs : DataFrame
            Must contain columns: host_col, cve_col, epss_col.
            Optional: kev_days_col (NaN or absent → KEV_recency = 0).
        hrs : Series
            Indexed by host_id (computer_id). Output of HygieneRiskScore.compute().

        Returns
        -------
        DataFrame
            Original pair columns plus:
            ``hrs_score``, ``kev_recency``, ``score``.
            Sorted descending by ``score``, then by EPSS desc, then cve_id asc (deterministic).
        """
        df = pairs.copy()

        # Attach HRS
        df["hrs_score"] = df[host_col].map(hrs).fillna(0.0)

        # Attach KEV recency
        if kev_days_col in df.columns:
            df["kev_recency"] = df[kev_days_col].apply(self.kev_recency)
        else:
            df["kev_recency"] = 0.0

        w = self.weights
        df["score"] = (
            w.alpha * df[epss_col]
            + w.beta * df["hrs_score"]
            + w.gamma * df["kev_recency"]
            + w.delta * df[epss_col] * df["hrs_score"]
        )

        return df.sort_values(
            by=["score", epss_col, cve_col],
            ascending=[False, False, True],
        ).reset_index(drop=True)

    def rank_pairs(
        self,
        pairs: pd.DataFrame,
        hrs: pd.Series,
        **kwargs,
    ) -> pd.DataFrame:
        """Alias for score_pairs — returns the ranked list."""
        return self.score_pairs(pairs, hrs, **kwargs)


# ---------------------------------------------------------------------------
# Baseline scorers
# ---------------------------------------------------------------------------

class EPSSOnlyScorer:
    """Rank pairs by EPSS(c) descending; ties broken by CVSS base score desc."""

    def rank_pairs(
        self,
        pairs: pd.DataFrame,
        *,
        epss_col: str = "epss_score",
        cvss_col: str = "cvss_base_score",
        cve_col: str = "cve_id",
    ) -> pd.DataFrame:
        tiebreak = cvss_col if cvss_col in pairs.columns else cve_col
        asc = [False, False, True] if tiebreak != cve_col else [False, True]
        cols = [epss_col, tiebreak] if tiebreak != epss_col else [epss_col]
        return pairs.sort_values(by=cols, ascending=asc[:len(cols)]).reset_index(drop=True)


class CVSSOnlyScorer:
    """Rank pairs by CVSS base score descending."""

    def rank_pairs(
        self,
        pairs: pd.DataFrame,
        *,
        cvss_col: str = "cvss_base_score",
        cve_col: str = "cve_id",
    ) -> pd.DataFrame:
        col = cvss_col if cvss_col in pairs.columns else cve_col
        return pairs.sort_values(by=col, ascending=False).reset_index(drop=True)


class HRSOnlyScorer:
    """Rank pairs by HRS(h) descending — host hygiene without CVE signal."""

    def rank_pairs(
        self,
        pairs: pd.DataFrame,
        hrs: pd.Series,
        *,
        host_col: str = "computer_id",
        epss_col: str = "epss_score",
    ) -> pd.DataFrame:
        df = pairs.copy()
        df["hrs_score"] = df[host_col].map(hrs).fillna(0.0)
        return df.sort_values(
            by=["hrs_score", epss_col],
            ascending=[False, False],
        ).reset_index(drop=True)


class RandomScorer:
    """Uniform random ranking (seeded by fleet seed for reproducibility)."""

    def rank_pairs(self, pairs: pd.DataFrame, *, seed: int = 42) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        df = pairs.copy()
        df["_rand"] = rng.random(len(df))
        return df.sort_values("_rand", ascending=False).drop(columns="_rand").reset_index(drop=True)
