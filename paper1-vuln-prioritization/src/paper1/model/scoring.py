"""Linear scoring with decomposable per-feature contributions.

    score = w_E*E + w_K*K + w_S*S + w_C*C + w_X*X + w_U*U - w_R*R

Every contribution is recorded so the score can be reconstructed (and
audited) feature by feature. The R contribution is stored negative.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from paper1.model.weights import FEATURE_COLUMNS, validate_weights

__all__ = [
    "compute_feature_contributions",
    "score_pairs_linear",
    "sort_ranking",
    "validate_feature_frame",
]


def validate_feature_frame(feature_frame: pd.DataFrame) -> None:
    """Raise if required feature columns are absent or contain NaN."""
    missing = set(["pair_id", *FEATURE_COLUMNS]) - set(feature_frame.columns)
    if missing:
        raise ValueError(f"feature_frame missing columns: {sorted(missing)}")
    nan_cols = [c for c in FEATURE_COLUMNS if feature_frame[c].isna().any()]
    if nan_cols:
        raise ValueError(f"feature_frame has NaN in feature columns: {nan_cols}")


def compute_feature_contributions(
    row: pd.Series | dict[str, float], weights: dict[str, float]
) -> dict[str, float]:
    """Per-feature contribution; R enters negative."""
    contrib: dict[str, float] = {}
    for f in FEATURE_COLUMNS:
        w = float(weights[f])
        v = float(row[f])
        contrib[f] = (-w * v) if f == "R" else (w * v)
    return contrib


def score_pairs_linear(
    feature_frame: pd.DataFrame, weights: dict[str, float]
) -> pd.DataFrame:
    """Score every pair; return contributions and the priority score.

    The input frame is not mutated. Output is sorted by priority_score
    descending then pair_id ascending.
    """
    validate_weights(weights)
    validate_feature_frame(feature_frame)

    df = feature_frame.copy()
    w = {f: float(weights[f]) for f in FEATURE_COLUMNS}

    contrib_cols: dict[str, np.ndarray] = {}
    for f in FEATURE_COLUMNS:
        sign = -1.0 if f == "R" else 1.0
        contrib_cols[f] = sign * w[f] * df[f].to_numpy(dtype=float)

    score = np.zeros(len(df), dtype=float)
    for f in FEATURE_COLUMNS:
        score = score + contrib_cols[f]

    feature_values = [
        {f: float(df.iloc[i][f]) for f in FEATURE_COLUMNS} for i in range(len(df))
    ]
    feature_contributions = [
        {f: float(contrib_cols[f][i]) for f in FEATURE_COLUMNS} for i in range(len(df))
    ]

    out = pd.DataFrame(
        {
            "pair_id": df["pair_id"].to_numpy(),
            "priority_score": score,
            **{f"contribution_{f}": contrib_cols[f] for f in FEATURE_COLUMNS},
            "feature_values": feature_values,
            "feature_contributions": feature_contributions,
        }
    )
    return sort_ranking(out, descending=True)


def sort_ranking(score_frame: pd.DataFrame, descending: bool = True) -> pd.DataFrame:
    """Deterministic sort: priority_score (desc) then pair_id (asc)."""
    return score_frame.sort_values(
        ["priority_score", "pair_id"], ascending=[not descending, True]
    ).reset_index(drop=True)
