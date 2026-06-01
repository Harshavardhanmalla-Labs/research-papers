"""Paper 1 weight-registry lock test (F7 §8).

Asserts the exact keys + numeric values of the four Paper-1 built-in vectors,
the registry's R-as-cost contract, and that Paper-2 vector registrations leave
the built-ins unchanged.
"""

from __future__ import annotations

import pytest

from paper1.model.weights import (
    _BUILTIN,
    FEATURE_COLUMNS,
    get_weights,
    list_weights,
    register_weights,
)

EXPECTED_HAND = {"E": 0.20, "K": 0.20, "S": 0.10, "C": 0.20, "X": 0.15, "U": 0.10, "R": 0.05}
PAPER1_BUILTIN_NAMES = ("w_uniform", "w_hand", "w_logit_placeholder", "w_lin_placeholder")


def test_feature_columns_are_locked():
    assert FEATURE_COLUMNS == ["E", "K", "S", "C", "X", "U", "R"]


def test_paper1_builtins_have_exact_keys():
    for name in PAPER1_BUILTIN_NAMES:
        assert set(_BUILTIN[name].keys()) == set(FEATURE_COLUMNS), name


def test_paper1_builtins_have_exact_raw_values():
    assert _BUILTIN["w_uniform"] == dict.fromkeys(FEATURE_COLUMNS, 1.0)
    assert _BUILTIN["w_hand"] == EXPECTED_HAND
    assert _BUILTIN["w_logit_placeholder"] == EXPECTED_HAND
    assert _BUILTIN["w_lin_placeholder"] == EXPECTED_HAND


def test_paper1_builtins_normalize_to_sum_one():
    for name in PAPER1_BUILTIN_NAMES:
        w = get_weights(name)
        assert abs(sum(w.values()) - 1.0) < 1e-12, name


def test_R_remains_non_negative_in_registry():
    for name in PAPER1_BUILTIN_NAMES:
        assert get_weights(name)["R"] >= 0.0, name


def test_paper1_builtins_cannot_be_overwritten():
    for name in PAPER1_BUILTIN_NAMES:
        with pytest.raises(ValueError):
            register_weights(name, dict(EXPECTED_HAND), overwrite=True)


def test_paper2_vector_registration_leaves_builtins_unchanged():
    # Snapshot before any Paper-2 registration is performed.
    before = {n: dict(_BUILTIN[n]) for n in PAPER1_BUILTIN_NAMES}
    from paper2_runtime.weights import register_paper2_fixed_priors
    register_paper2_fixed_priors()
    # All four new Paper-2 names are registered.
    names = set(list_weights())
    assert "w_epss_dominant" in names
    assert "w_cvss_dominant" in names
    assert "w_kev_dominant" in names
    assert "w_context_dominant" in names
    # Built-ins are byte-identical to the snapshot.
    after = {n: dict(_BUILTIN[n]) for n in PAPER1_BUILTIN_NAMES}
    assert after == before


def test_no_paper2_code_calls_register_calibrated_weights():
    """K1 forbid: search ``paper2_runtime/`` source for register_calibrated_weights."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1] / "paper2_runtime"
    for py in root.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        assert "register_calibrated_weights(" not in text, (
            f"{py} calls register_calibrated_weights — forbidden by K1"
        )
