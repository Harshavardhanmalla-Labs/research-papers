"""Weight registry tests."""

from __future__ import annotations

import pytest

from paper1.model.weights import (
    FEATURE_COLUMNS,
    ablate_weight,
    get_weights,
    list_weights,
    normalize_weights,
    register_weights,
    validate_weights,
)


def test_builtins_present():
    names = set(list_weights())
    assert {"w_uniform", "w_hand", "w_logit_placeholder", "w_lin_placeholder"} <= names


def test_get_weights_returns_normalized():
    w = get_weights("w_hand")
    assert abs(sum(w.values()) - 1.0) < 1e-9
    assert set(w.keys()) == set(FEATURE_COLUMNS)


def test_w_uniform_is_equal_weighted():
    w = get_weights("w_uniform")
    for f in FEATURE_COLUMNS:
        assert abs(w[f] - 1.0 / 7.0) < 1e-9


def test_get_weights_returns_copy_not_registry():
    a = get_weights("w_hand")
    a["E"] = 999.0
    b = get_weights("w_hand")
    assert b["E"] != 999.0


def test_get_weights_unknown_raises():
    with pytest.raises(ValueError):
        get_weights("does_not_exist")


def test_normalize_sums_to_one():
    w = normalize_weights(dict.fromkeys(FEATURE_COLUMNS, 2.0))
    assert abs(sum(w.values()) - 1.0) < 1e-9


def test_validate_negative_weight_fails():
    bad = dict.fromkeys(FEATURE_COLUMNS, 1.0)
    bad["E"] = -0.5
    with pytest.raises(ValueError):
        validate_weights(bad)


def test_validate_missing_feature_fails():
    bad = {f: 1.0 for f in FEATURE_COLUMNS if f != "R"}
    with pytest.raises(ValueError):
        validate_weights(bad)


def test_validate_extra_feature_fails():
    bad = dict.fromkeys(FEATURE_COLUMNS, 1.0)
    bad["Z"] = 1.0
    with pytest.raises(ValueError):
        validate_weights(bad)


def test_ablate_c_zeroes_and_renormalizes():
    w = get_weights("w_hand")
    ab = ablate_weight(w, "C")
    assert ab["C"] == 0.0
    assert abs(sum(ab.values()) - 1.0) < 1e-9


def test_ablate_x_zeroes_and_renormalizes():
    w = get_weights("w_hand")
    ab = ablate_weight(w, "X")
    assert ab["X"] == 0.0
    assert abs(sum(ab.values()) - 1.0) < 1e-9


def test_ablate_unknown_feature_raises():
    with pytest.raises(ValueError):
        ablate_weight(get_weights("w_hand"), "Z")


def test_register_weights_and_retrieve():
    register_weights("w_test_custom", dict.fromkeys(FEATURE_COLUMNS, 1.0), overwrite=True)
    w = get_weights("w_test_custom")
    assert abs(sum(w.values()) - 1.0) < 1e-9


def test_register_over_builtin_fails():
    with pytest.raises(ValueError):
        register_weights("w_hand", dict.fromkeys(FEATURE_COLUMNS, 1.0))


def test_register_duplicate_without_overwrite_fails():
    register_weights("w_dup_test", dict.fromkeys(FEATURE_COLUMNS, 1.0), overwrite=True)
    with pytest.raises(ValueError):
        register_weights("w_dup_test", dict.fromkeys(FEATURE_COLUMNS, 1.0))
