"""Linear scoring tests."""

from __future__ import annotations

import pandas as pd
import pytest

from paper1.model.scoring import (
    compute_feature_contributions,
    score_pairs_linear,
    sort_ranking,
    validate_feature_frame,
)
from paper1.model.weights import FEATURE_COLUMNS, get_weights


def _feature_frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _equal_weights() -> dict[str, float]:
    return dict.fromkeys(FEATURE_COLUMNS, 1.0 / 7.0)


def test_score_formula_on_toy_data():
    # Single pair, all features 1.0, equal weights.
    ff = _feature_frame(
        [{"pair_id": "P1", "E": 1.0, "K": 1.0, "S": 1.0, "C": 1.0, "X": 1.0, "U": 1.0, "R": 1.0}]
    )
    w = _equal_weights()
    out = score_pairs_linear(ff, w)
    # score = (1/7)*(E+K+S+C+X+U) - (1/7)*R = (1/7)*5 = 5/7
    assert out.iloc[0]["priority_score"] == pytest.approx(5.0 / 7.0)


def test_r_contribution_is_negative():
    ff = _feature_frame(
        [{"pair_id": "P1", "E": 0.0, "K": 0.0, "S": 0.0, "C": 0.0, "X": 0.0, "U": 0.0, "R": 1.0}]
    )
    out = score_pairs_linear(ff, _equal_weights())
    assert out.iloc[0]["contribution_R"] < 0
    assert out.iloc[0]["priority_score"] < 0


def test_contributions_sum_to_priority_score():
    ff = _feature_frame(
        [{"pair_id": "P1", "E": 0.3, "K": 1.0, "S": 0.8, "C": 0.6, "X": 0.5, "U": 0.4, "R": 0.7}]
    )
    out = score_pairs_linear(ff, get_weights("w_hand"))
    contrib_sum = sum(out.iloc[0][f"contribution_{f}"] for f in FEATURE_COLUMNS)
    assert contrib_sum == pytest.approx(out.iloc[0]["priority_score"])


def test_compute_feature_contributions_helper():
    w = get_weights("w_hand")
    row = {"E": 0.5, "K": 1.0, "S": 0.5, "C": 0.5, "X": 0.5, "U": 0.5, "R": 1.0}
    contrib = compute_feature_contributions(row, w)
    assert contrib["R"] == pytest.approx(-w["R"] * 1.0)
    assert contrib["E"] == pytest.approx(w["E"] * 0.5)


def test_sorting_breaks_ties_by_pair_id():
    ff = _feature_frame(
        [
            {"pair_id": "P-b", "E": 0.5, "K": 0.0, "S": 0.0, "C": 0.0, "X": 0.0, "U": 0.0, "R": 0.0},
            {"pair_id": "P-a", "E": 0.5, "K": 0.0, "S": 0.0, "C": 0.0, "X": 0.0, "U": 0.0, "R": 0.0},
        ]
    )
    out = score_pairs_linear(ff, _equal_weights())
    # Equal scores -> pair_id ascending.
    assert out["pair_id"].tolist() == ["P-a", "P-b"]


def test_input_frame_not_mutated():
    ff = _feature_frame(
        [{"pair_id": "P1", "E": 0.5, "K": 0.0, "S": 0.0, "C": 0.0, "X": 0.0, "U": 0.0, "R": 0.0}]
    )
    before = ff.copy(deep=True)
    score_pairs_linear(ff, _equal_weights())
    pd.testing.assert_frame_equal(ff, before)


def test_missing_feature_column_raises():
    ff = _feature_frame([{"pair_id": "P1", "E": 0.5}])
    with pytest.raises(ValueError):
        score_pairs_linear(ff, _equal_weights())


def test_nan_feature_raises():
    ff = _feature_frame(
        [{"pair_id": "P1", "E": float("nan"), "K": 0.0, "S": 0.0, "C": 0.0, "X": 0.0, "U": 0.0, "R": 0.0}]
    )
    with pytest.raises(ValueError):
        validate_feature_frame(ff)


def test_higher_score_ranks_first():
    ff = _feature_frame(
        [
            {"pair_id": "P-low", "E": 0.1, "K": 0.0, "S": 0.0, "C": 0.0, "X": 0.0, "U": 0.0, "R": 0.0},
            {"pair_id": "P-high", "E": 0.9, "K": 0.0, "S": 0.0, "C": 0.0, "X": 0.0, "U": 0.0, "R": 0.0},
        ]
    )
    out = score_pairs_linear(ff, _equal_weights())
    assert out.iloc[0]["pair_id"] == "P-high"


def test_sort_ranking_ascending_option():
    frame = pd.DataFrame({"pair_id": ["a", "b"], "priority_score": [1.0, 2.0]})
    out = sort_ranking(frame, descending=False)
    assert out["pair_id"].tolist() == ["a", "b"]
