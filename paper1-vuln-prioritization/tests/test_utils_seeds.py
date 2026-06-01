"""Deterministic seed derivation tests."""

from __future__ import annotations

import numpy as np
import pytest

from paper1.utils.seeds import derive_subseed, derive_subseeds, make_rng


def test_same_master_and_name_gives_same_subseed():
    a = derive_subseed(20260601, "fleet")
    b = derive_subseed(20260601, "fleet")
    assert a == b


def test_different_names_give_different_subseeds():
    a = derive_subseed(20260601, "fleet")
    b = derive_subseed(20260601, "software")
    assert a != b


def test_different_master_gives_different_subseed():
    a = derive_subseed(1, "fleet")
    b = derive_subseed(2, "fleet")
    assert a != b


def test_subseed_is_64_bit_unsigned():
    s = derive_subseed(20260601, "fleet")
    assert 0 <= s < 2**64


def test_derive_subseeds_returns_unique_per_name():
    out = derive_subseeds(20260601, ["a", "b", "c"])
    assert set(out.keys()) == {"a", "b", "c"}
    assert len(set(out.values())) == 3


def test_derive_subseeds_rejects_duplicate_names():
    with pytest.raises(ValueError):
        derive_subseeds(20260601, ["a", "a"])


def test_negative_master_seed_rejected():
    with pytest.raises(ValueError):
        derive_subseed(-1, "fleet")


def test_empty_name_rejected():
    with pytest.raises(ValueError):
        derive_subseed(1, "")


def test_master_must_be_int():
    with pytest.raises(TypeError):
        derive_subseed("1", "fleet")  # type: ignore[arg-type]


def test_make_rng_is_deterministic():
    rng_a = make_rng(42)
    rng_b = make_rng(42)
    a = rng_a.random(10)
    b = rng_b.random(10)
    assert np.array_equal(a, b)


def test_make_rng_different_seeds_produce_different_streams():
    a = make_rng(42).random(10)
    b = make_rng(43).random(10)
    assert not np.array_equal(a, b)


def test_make_rng_rejects_negative_seed():
    with pytest.raises(ValueError):
        make_rng(-1)


def test_make_rng_rejects_non_int_seed():
    with pytest.raises(TypeError):
        make_rng(1.5)  # type: ignore[arg-type]


def test_cross_machine_stability_known_vector():
    """Sub-seed for (20260601, 'fleet') is fixed by the SHA-256 derivation.

    If this test ever fails, the seed derivation has changed and downstream
    reproducibility breaks. Update only with a deliberate version bump.
    """
    # Computed once: int.from_bytes(sha256(b"20260601|fleet").digest()[:8], 'big')
    expected = int.from_bytes(
        __import__("hashlib").sha256(b"20260601|fleet").digest()[:8],
        byteorder="big",
        signed=False,
    )
    assert derive_subseed(20260601, "fleet") == expected
