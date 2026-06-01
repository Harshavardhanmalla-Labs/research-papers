"""Telemetry freshness / missingness tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from paper1.synthetic.telemetry import (
    TELEMETRY_SOURCES,
    sample_last_seen_per_source,
    sample_missing_telemetry_fields,
    telemetry_staleness_flags,
)
from paper1.utils.seeds import make_rng


def test_last_seen_never_after_t0():
    rng = make_rng(1)
    t0 = date(2026, 5, 31)
    for _ in range(50):
        out = sample_last_seen_per_source(t0, "standard_workstation", rng)
        for source, ts in out.items():
            assert ts.tzinfo is not None
            assert ts <= datetime.combine(t0, datetime.min.time().replace(hour=9), tzinfo=UTC)


def test_last_seen_includes_all_sources():
    rng = make_rng(1)
    t0 = date(2026, 5, 31)
    out = sample_last_seen_per_source(t0, "standard_workstation", rng)
    assert set(out.keys()) == set(TELEMETRY_SOURCES)


def test_last_seen_mobile_devices_tend_to_be_more_stale():
    rng = make_rng(1)
    t0 = date(2026, 5, 31)
    workstation_samples = []
    mobile_samples = []
    for _ in range(200):
        workstation_samples.append(
            sample_last_seen_per_source(t0, "standard_workstation", rng)
        )
        mobile_samples.append(sample_last_seen_per_source(t0, "mobile_device", rng))

    def _mean_age_seconds(samples):
        cutoff = datetime.combine(t0, datetime.min.time().replace(hour=9), tzinfo=UTC)
        ages = [(cutoff - s["inventory"]).total_seconds() for s in samples]
        return sum(ages) / len(ages)

    assert _mean_age_seconds(mobile_samples) > _mean_age_seconds(workstation_samples)


def test_missingness_deterministic():
    rng_a = make_rng(7)
    rng_b = make_rng(7)
    a = sample_missing_telemetry_fields(TELEMETRY_SOURCES, 0.5, rng_a)
    b = sample_missing_telemetry_fields(TELEMETRY_SOURCES, 0.5, rng_b)
    assert a == b


def test_missingness_zero_rate_returns_empty():
    rng = make_rng(1)
    out = sample_missing_telemetry_fields(TELEMETRY_SOURCES, 0.0, rng)
    assert out == []


def test_missingness_full_rate_returns_all():
    rng = make_rng(1)
    out = sample_missing_telemetry_fields(TELEMETRY_SOURCES, 1.0, rng)
    assert set(out) == set(TELEMETRY_SOURCES)


def test_missingness_rate_out_of_range_raises():
    rng = make_rng(1)
    with pytest.raises(ValueError):
        sample_missing_telemetry_fields(TELEMETRY_SOURCES, 1.5, rng)


def test_staleness_flag_emitted_when_old():
    t0 = date(2026, 5, 31)
    cutoff = datetime.combine(t0, datetime.min.time(), tzinfo=UTC)
    last = {
        "inventory": cutoff - timedelta(days=14),
        "endpoint_agent": cutoff - timedelta(days=1),
        "identity": cutoff - timedelta(days=20),
    }
    flags = telemetry_staleness_flags(last, t0, stale_threshold_days=7)
    assert "inventory>7d" in flags
    assert "identity>7d" in flags
    assert "endpoint_agent>7d" not in flags


def test_staleness_flags_sorted_and_deterministic():
    t0 = date(2026, 5, 31)
    cutoff = datetime.combine(t0, datetime.min.time(), tzinfo=UTC)
    last = {
        "z_source": cutoff - timedelta(days=30),
        "a_source": cutoff - timedelta(days=30),
    }
    flags = telemetry_staleness_flags(last, t0)
    assert flags == sorted(flags)
