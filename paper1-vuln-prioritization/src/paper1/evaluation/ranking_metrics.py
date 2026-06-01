"""Ranking-quality metrics: precision@k, recall@k, nDCG@k, rank churn.

Censored (pd.NA) labels are excluded from both numerator and denominator.
Lower ``rank`` means higher priority; ties break by ``pair_id`` ascending.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from paper1.evaluation.metrics import is_censored, is_positive, normalize_labels

__all__ = [
    "ndcg_at_k",
    "precision_at_k",
    "rank_churn",
    "ranking_curve_at_ks",
    "recall_at_k",
]


def _ordered_pairs(ranking: pd.DataFrame) -> list[str]:
    if "pair_id" not in ranking.columns or "rank" not in ranking.columns:
        raise ValueError("ranking must have 'pair_id' and 'rank' columns")
    if ranking["pair_id"].duplicated().any():
        raise ValueError("ranking contains duplicate pair_id values")
    ordered = ranking.sort_values(["rank", "pair_id"]).reset_index(drop=True)
    return [str(p) for p in ordered["pair_id"]]


def precision_at_k(
    ranking: pd.DataFrame, labels, k: int, label_col: str = "label"
) -> float:
    lab = normalize_labels(labels, label_col)
    pairs = _ordered_pairs(ranking)[: max(0, k)]
    considered = [(p, lab.get(p, pd.NA)) for p in pairs]
    non_censored = [(p, v) for p, v in considered if not is_censored(v)]
    if not non_censored:
        return np.nan
    pos = sum(1 for _, v in non_censored if is_positive(v))
    return pos / len(non_censored)


def recall_at_k(
    ranking: pd.DataFrame, labels, k: int, label_col: str = "label"
) -> float:
    lab = normalize_labels(labels, label_col)
    total_pos = sum(1 for v in lab.values() if is_positive(v))
    if total_pos == 0:
        return np.nan
    pairs = _ordered_pairs(ranking)[: max(0, k)]
    pos_in_topk = sum(1 for p in pairs if is_positive(lab.get(p, pd.NA)))
    return pos_in_topk / total_pos


def ndcg_at_k(
    ranking: pd.DataFrame, labels, k: int, label_col: str = "label"
) -> float:
    lab = normalize_labels(labels, label_col)
    # Exclude censored pairs entirely; positions are among non-censored.
    pairs = [p for p in _ordered_pairs(ranking) if not is_censored(lab.get(p, pd.NA))]
    total_pos = sum(1 for p in pairs if is_positive(lab.get(p, pd.NA)))
    if total_pos == 0:
        return np.nan
    kk = max(0, k)
    topk = pairs[:kk]
    dcg = 0.0
    for i, p in enumerate(topk, start=1):
        if is_positive(lab.get(p, pd.NA)):
            dcg += 1.0 / math.log2(i + 1)
    ideal_n = min(total_pos, kk)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_n + 1))
    if idcg == 0:
        return np.nan
    return dcg / idcg


def ranking_curve_at_ks(
    ranking: pd.DataFrame,
    labels,
    ks: tuple[int, ...] = (10, 50, 100, 500, 1000),
    label_col: str = "label",
) -> pd.DataFrame:
    rows = []
    for k in ks:
        rows.append(
            {
                "k": k,
                "precision": precision_at_k(ranking, labels, k, label_col),
                "recall": recall_at_k(ranking, labels, k, label_col),
                "ndcg": ndcg_at_k(ranking, labels, k, label_col),
            }
        )
    return pd.DataFrame(rows, columns=["k", "precision", "recall", "ndcg"])


def rank_churn(prev_ranking: pd.DataFrame, curr_ranking: pd.DataFrame) -> float:
    """Mean absolute rank change for pairs present in both rankings."""
    for df, name in ((prev_ranking, "prev"), (curr_ranking, "curr")):
        if "pair_id" not in df.columns or "rank" not in df.columns:
            raise ValueError(f"{name}_ranking must have 'pair_id' and 'rank' columns")
    prev = dict(zip(prev_ranking["pair_id"], prev_ranking["rank"], strict=True))
    curr = dict(zip(curr_ranking["pair_id"], curr_ranking["rank"], strict=True))
    common = set(prev) & set(curr)
    if not common:
        return np.nan
    diffs = [abs(int(curr[p]) - int(prev[p])) for p in common]
    return float(np.mean(diffs))
