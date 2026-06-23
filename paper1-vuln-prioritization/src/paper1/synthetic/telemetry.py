"""Telemetry freshness and missingness sampling."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime, time, timedelta

import numpy as np

__all__ = [
    "TELEMETRY_SOURCES",
    "sample_last_seen_per_source",
    "sample_missing_telemetry_fields",
    "telemetry_staleness_flags",
]


TELEMETRY_SOURCES = ("inventory", "endpoint_agent", "identity", "network", "cmdb")


def sample_last_seen_per_source(
    t0: date,
    host_role: str,
    rng: np.random.Generator,
) -> dict[str, datetime]:
    """Generate per-source last-seen datetimes; all <= t0.

    Mobile devices are sampled with longer typical staleness than wired
    endpoints because real fleets see them less frequently.
    """
    base = datetime.combine(t0, time(hour=9), tzinfo=UTC)
    out: dict[str, datetime] = {}
    for source in TELEMETRY_SOURCES:
        if host_role == "mobile_device":
            mean_days_back = 3.0
        elif host_role == "kiosk":
            mean_days_back = 2.0
        else:
            mean_days_back = 0.5
        days_back = float(rng.exponential(mean_days_back))
        days_back = max(0.0, min(days_back, 30.0))
        ts = base - timedelta(
            days=int(days_back),
            hours=int((days_back - int(days_back)) * 24),
        )
        if ts > base:
            ts = base
        out[source] = ts
    return out


def sample_missing_telemetry_fields(
    fields: Iterable[str],
    missingness_rate: float,
    rng: np.random.Generator,
) -> list[str]:
    """Return the subset of `fields` that should be treated as missing."""
    if not (0.0 <= missingness_rate <= 1.0):
        raise ValueError(f"missingness_rate must be in [0, 1]; got {missingness_rate}")
    return [f for f in sorted(set(fields)) if rng.random() < missingness_rate]


def telemetry_staleness_flags(
    last_seen_per_source: dict[str, datetime],
    t0: date,
    stale_threshold_days: int = 7,
) -> list[str]:
    """Emit a sorted list of `source>Nd` flags for any stale source."""
    threshold = datetime.combine(t0, time(hour=0), tzinfo=UTC) - timedelta(
        days=stale_threshold_days
    )
    flags: list[str] = []
    for source in sorted(last_seen_per_source):
        if last_seen_per_source[source] < threshold:
            flags.append(f"{source}>{stale_threshold_days}d")
    return flags
