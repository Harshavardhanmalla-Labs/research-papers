"""Patch state and patch-lag tests."""

from __future__ import annotations

from datetime import date

import pytest

from paper1.audit.schema import PatchState
from paper1.synthetic.catalogs import load_host_type_defaults
from paper1.synthetic.patch_state import (
    MAX_PATCH_LAG_DAYS,
    derive_patch_state,
    sample_patch_lag_days,
    sample_scan_time,
)
from paper1.utils.seeds import make_rng


def test_patch_lag_non_negative_and_capped():
    defaults = load_host_type_defaults()
    rng = make_rng(1)
    for _ in range(100):
        lag = sample_patch_lag_days("kiosk", defaults, rng)
        assert 0 <= lag <= MAX_PATCH_LAG_DAYS


def test_patch_lag_deterministic():
    defaults = load_host_type_defaults()
    a = sample_patch_lag_days("standard_workstation", defaults, make_rng(42))
    b = sample_patch_lag_days("standard_workstation", defaults, make_rng(42))
    assert a == b


def test_patch_lag_long_tail_present():
    defaults = load_host_type_defaults()
    rng = make_rng(7)
    samples = [sample_patch_lag_days("kiosk", defaults, rng) for _ in range(500)]
    mean = sum(samples) / len(samples)
    # Some samples must exceed the mean by a wide margin (long-tail behavior).
    assert max(samples) > 2 * mean


def test_scan_time_is_utc_and_not_in_future():
    rng = make_rng(1)
    t0 = date(2026, 5, 31)
    for _ in range(50):
        ts = sample_scan_time(t0, rng)
        assert ts.tzinfo is not None
        assert ts.utcoffset().total_seconds() == 0
        assert ts.date() <= t0


def test_derive_patch_state_validates():
    rng = make_rng(3)
    ps = derive_patch_state(["KB1234"], date(2026, 5, 31), "sccm", rng)
    assert isinstance(ps, PatchState)
    assert ps.kbs_installed == ["KB1234"]
    assert ps.scan_source == "sccm"
    assert ps.last_scan.date() <= date(2026, 5, 31)


def test_patch_lag_unknown_role_raises():
    defaults = load_host_type_defaults()
    rng = make_rng(1)
    with pytest.raises(KeyError):
        sample_patch_lag_days("not_a_role", defaults, rng)
