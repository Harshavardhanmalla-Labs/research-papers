"""Ranking-quality metric tests with hand-computed values."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from paper1.evaluation.ranking_metrics import (
    ndcg_at_k,
    precision_at_k,
    rank_churn,
    ranking_curve_at_ks,
    recall_at_k,
)


def _ranking(pair_ids):
    return pd.DataFrame(
        {"pair_id": pair_ids, "rank": list(range(1, len(pair_ids) + 1)),
         "priority_score": [1.0 - 0.01 * i for i in range(len(pair_ids))]}
    )


def _labels(mapping):
    return pd.Series(mapping, dtype="object")


def test_precision_at_k_toy():
    r = _ranking(["a", "b", "c", "d"])
    labels = _labels({"a": True, "b": False, "c": True, "d": False})
    # top-3: a(1), b(0), c(1) -> 2/3
    assert precision_at_k(r, labels, 3) == pytest.approx(2 / 3)


def test_recall_at_k_toy():
    r = _ranking(["a", "b", "c", "d"])
    labels = _labels({"a": True, "b": False, "c": True, "d": True})
    # total positives = 3; top-2 (a,b) has 1 positive -> 1/3
    assert recall_at_k(r, labels, 2) == pytest.approx(1 / 3)


def test_ndcg_perfect_is_one():
    r = _ranking(["a", "b", "c"])
    labels = _labels({"a": True, "b": True, "c": False})
    # positives at top -> nDCG == 1
    assert ndcg_at_k(r, labels, 3) == pytest.approx(1.0)


def test_ndcg_reversed_lower_than_perfect():
    perfect = _ranking(["a", "b", "c"])
    reversed_ = _ranking(["c", "b", "a"])
    labels = _labels({"a": True, "b": True, "c": False})
    assert ndcg_at_k(reversed_, labels, 3) < ndcg_at_k(perfect, labels, 3)


def test_ndcg_value_hand_computed():
    # ranking a,b with a=0,b=1: DCG = 0/log2(2) + 1/log2(3) = 1/1.58496
    r = _ranking(["a", "b"])
    labels = _labels({"a": False, "b": True})
    dcg = 1.0 / math.log2(3)
    idcg = 1.0 / math.log2(2)  # one positive ideally at position 1
    assert ndcg_at_k(r, labels, 2) == pytest.approx(dcg / idcg)


def test_censored_labels_excluded_precision():
    r = _ranking(["a", "b", "c"])
    labels = _labels({"a": True, "b": pd.NA, "c": False})
    # top-3 non-censored: a(1), c(0) -> 1/2
    assert precision_at_k(r, labels, 3) == pytest.approx(0.5)


def test_k_larger_than_rows():
    r = _ranking(["a", "b"])
    labels = _labels({"a": True, "b": False})
    assert precision_at_k(r, labels, 100) == pytest.approx(0.5)


def test_no_positives_recall_nan():
    r = _ranking(["a", "b"])
    labels = _labels({"a": False, "b": False})
    assert np.isnan(recall_at_k(r, labels, 2))


def test_all_censored_precision_nan():
    r = _ranking(["a", "b"])
    labels = _labels({"a": pd.NA, "b": pd.NA})
    assert np.isnan(precision_at_k(r, labels, 2))


def test_duplicate_pair_id_raises():
    r = pd.DataFrame({"pair_id": ["a", "a"], "rank": [1, 2], "priority_score": [1.0, 0.9]})
    with pytest.raises(ValueError):
        precision_at_k(r, _labels({"a": True}), 2)


def test_labels_as_dataframe():
    r = _ranking(["a", "b"])
    labels_df = pd.DataFrame({"pair_id": ["a", "b"], "label": [True, False]})
    assert precision_at_k(r, labels_df, 2) == pytest.approx(0.5)


def test_ranking_curve_columns():
    r = _ranking(["a", "b", "c"])
    labels = _labels({"a": True, "b": False, "c": True})
    curve = ranking_curve_at_ks(r, labels, ks=(1, 2, 3))
    assert list(curve.columns) == ["k", "precision", "recall", "ndcg"]
    assert len(curve) == 3


def test_rank_churn_identical_zero():
    a = _ranking(["x", "y", "z"])
    assert rank_churn(a, a) == pytest.approx(0.0)


def test_rank_churn_hand_computed():
    prev = pd.DataFrame({"pair_id": ["a", "b", "c"], "rank": [1, 2, 3]})
    curr = pd.DataFrame({"pair_id": ["a", "b", "c"], "rank": [2, 1, 3]})
    # |2-1| + |1-2| + |3-3| = 2; mean = 2/3
    assert rank_churn(prev, curr) == pytest.approx(2 / 3)


def test_rank_churn_no_overlap_nan():
    prev = pd.DataFrame({"pair_id": ["a"], "rank": [1]})
    curr = pd.DataFrame({"pair_id": ["b"], "rank": [1]})
    assert np.isnan(rank_churn(prev, curr))
