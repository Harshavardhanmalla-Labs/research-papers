"""
CAP-G scorer (Paper 11).

    S_CAP-G(h, c) = S_HygienePrio(h, c) · (1 + rho · ACS(h))

Re-uses the calibrated Paper-4 HygienePrio scorer verbatim (alpha=0.7, beta=0.5,
gamma=0.1, delta=0.2) and multiplies by a host context multiplier driven by the
Asset Context Score (PAPER11_PROTOCOL.md §5.2). rho is the context-emphasis
hyperparameter calibrated on held-out seeds (§5.3).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Wire in the Paper 4 HygienePrio package (re-used, not reimplemented).
_REPO = Path(__file__).resolve().parents[3]
_P4 = Path(__file__).resolve().parents[1]  # vendored hygieneprio in local src
if str(_P4) not in sys.path:
    sys.path.insert(0, str(_P4))

from hygieneprio.scorer import (  # noqa: E402
    HygienePrioScorer,
    ScorerWeights,
    EPSSOnlyScorer,
    CVSSOnlyScorer,
    HRSOnlyScorer,
    RandomScorer,
)

# Calibrated Paper-4 weights, fixed and re-used (PAPER11_PROTOCOL.md §5.2).
HYGIENEPRIO_WEIGHTS = ScorerWeights(alpha=0.7, beta=0.5, gamma=0.1, delta=0.2)


@dataclass
class CAPGConfig:
    rho: float = 2.0  # context-emphasis; calibrated on held-out seeds (§5.3)


class CAPGScorer:
    """
    Context-Aware Prioritization for Government fleets.

    Parameters
    ----------
    rho : float
        Context-emphasis hyperparameter (>= 0). 0 reduces CAP-G to HygienePrio.
    scorer_weights : ScorerWeights, optional
        HygienePrio weights. Defaults to the calibrated Paper-4 weights.
    """

    def __init__(
        self,
        rho: float = 2.0,
        scorer_weights: Optional[ScorerWeights] = None,
    ) -> None:
        if rho < 0:
            raise ValueError(f"rho must be non-negative, got {rho}")
        self.rho = rho
        self._hp = HygienePrioScorer(weights=scorer_weights or HYGIENEPRIO_WEIGHTS)

    def rank_pairs(
        self,
        pairs: pd.DataFrame,
        hrs: pd.Series,
        acs: pd.Series,
        *,
        host_col: str = "computer_id",
        cve_col: str = "cve_id",
        epss_col: str = "epss_score",
    ) -> pd.DataFrame:
        """
        Score and rank (host, CVE) pairs by S_CAP-G.

        Returns the pairs DataFrame with added columns hp_score, acs, context_mult,
        score; sorted descending by score then EPSS then cve_id (deterministic).
        Any extra columns on ``pairs`` (e.g. _label) are preserved.
        """
        # Base HygienePrio score (does its own sort; we re-sort after multiplying).
        scored = self._hp.score_pairs(
            pairs, hrs, host_col=host_col, cve_col=cve_col, epss_col=epss_col
        )
        scored = scored.rename(columns={"score": "hp_score"})
        scored["acs"] = scored[host_col].map(acs).fillna(0.0)
        scored["context_mult"] = 1.0 + self.rho * scored["acs"]
        scored["score"] = scored["hp_score"] * scored["context_mult"]
        return scored.sort_values(
            by=["score", epss_col, cve_col],
            ascending=[False, False, True],
        ).reset_index(drop=True)


class ContextOnlyScorer:
    """Rank pairs by ACS(h) alone (no exploit signal). EPSS used only as tiebreak."""

    def rank_pairs(
        self,
        pairs: pd.DataFrame,
        acs: pd.Series,
        *,
        host_col: str = "computer_id",
        epss_col: str = "epss_score",
    ) -> pd.DataFrame:
        df = pairs.copy()
        df["acs"] = df[host_col].map(acs).fillna(0.0)
        return df.sort_values(
            by=["acs", epss_col],
            ascending=[False, False],
        ).reset_index(drop=True)


# Re-export Paper-4 baseline scorers so the evaluator imports from one module.
__all__ = [
    "CAPGScorer",
    "CAPGConfig",
    "ContextOnlyScorer",
    "HygienePrioScorer",
    "ScorerWeights",
    "EPSSOnlyScorer",
    "CVSSOnlyScorer",
    "HRSOnlyScorer",
    "RandomScorer",
    "HYGIENEPRIO_WEIGHTS",
]
