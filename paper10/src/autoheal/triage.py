"""Stage 3: Triage — classify each (host, CVE) pair into AUTO / REVIEW / DEFER.

Thresholds are pre-registered (paper10/design/PAPER10_PROTOCOL.md §3 Stage 3).
"""
from __future__ import annotations
from enum import Enum
from typing import Optional

import pandas as pd


class TriageClass(str, Enum):
    AUTO   = "AUTO"
    REVIEW = "REVIEW"
    DEFER  = "DEFER"


# Pre-registered thresholds (locked 2026-06-05).
SCORE_AUTO_THRESHOLD   = 0.80
SCORE_REVIEW_THRESHOLD = 0.50
# Hosts classified CRITICAL never get AUTO-remediated.
CRITICAL_CRITICALITIES = {"CRITICAL"}


def classify(
    score: float,
    host_criticality: str,
    has_test_suite: bool = True,
    has_blocking_config: bool = False,
    is_business_hours: bool = False,
) -> TriageClass:
    """Decide AUTO / REVIEW / DEFER for one (host, CVE) pair.

    The decision tree is the locked rule from the protocol:

    AUTO  iff score >= 0.80 AND host_criticality != CRITICAL
              AND has_test_suite AND not has_blocking_config

    REVIEW if score in [0.50, 0.80), OR host_criticality == CRITICAL,
              OR is_business_hours

    DEFER  if score < 0.50 OR has_blocking_config (no test suite implies blocking)
    """
    if score < SCORE_REVIEW_THRESHOLD or has_blocking_config:
        return TriageClass.DEFER

    if (score >= SCORE_AUTO_THRESHOLD
            and host_criticality not in CRITICAL_CRITICALITIES
            and has_test_suite
            and not has_blocking_config
            and not is_business_hours):
        return TriageClass.AUTO

    return TriageClass.REVIEW


def classify_dataframe(
    pairs: pd.DataFrame,
    score_col: str = "hp_score",
    criticality_col: str = "asset_criticality",
    has_test_suite: Optional[pd.Series] = None,
    has_blocking_config: Optional[pd.Series] = None,
) -> pd.Series:
    """Vectorised triage classification on a DataFrame of pairs.

    Defaults: has_test_suite=True, has_blocking_config=False
    (the configuration AutoHeal would expect after CI/CD integration).
    """
    n = len(pairs)
    if has_test_suite is None:
        has_test_suite = pd.Series([True] * n, index=pairs.index)
    if has_blocking_config is None:
        has_blocking_config = pd.Series([False] * n, index=pairs.index)

    out = []
    for i in range(n):
        out.append(classify(
            score=float(pairs.iloc[i][score_col]),
            host_criticality=str(pairs.iloc[i][criticality_col]),
            has_test_suite=bool(has_test_suite.iloc[i]),
            has_blocking_config=bool(has_blocking_config.iloc[i]),
            is_business_hours=False,
        ))
    return pd.Series(out, index=pairs.index, name="triage")
