"""Patch-state and patch-lag sampling."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Any

import numpy as np

from paper1.audit.schema import PatchState

__all__ = [
    "MAX_PATCH_LAG_DAYS",
    "derive_patch_state",
    "sample_patch_lag_days",
    "sample_scan_time",
]


MAX_PATCH_LAG_DAYS = 365


def sample_patch_lag_days(
    host_role: str,
    defaults: dict[str, Any],
    rng: np.random.Generator,
) -> int:
    """Sample a non-negative integer patch lag, capped at MAX_PATCH_LAG_DAYS.

    Uses a lognormal distribution parameterized by per-role mean and sigma.
    """
    role_cfg = defaults["host_types"][host_role]
    mean_days = float(role_cfg["patch_lag_mean_days"])
    sigma = float(role_cfg.get("patch_lag_sigma", 0.6))
    if mean_days <= 0:
        return 0
    # Convert "mean of resulting distribution ≈ mean_days" into the mu
    # parameter of the lognormal. For a lognormal(mu, sigma), the mean is
    # exp(mu + sigma^2 / 2). Solving for mu:
    mu = float(np.log(mean_days) - 0.5 * sigma * sigma)
    sample = float(rng.lognormal(mean=mu, sigma=sigma))
    return round(max(0.0, min(sample, MAX_PATCH_LAG_DAYS)))


def sample_scan_time(t0: date, rng: np.random.Generator) -> datetime:
    """Sample the host's last scan time within the prior 7 days of t0."""
    days_back = int(rng.integers(0, 7))
    hours = int(rng.integers(0, 24))
    minutes = int(rng.integers(0, 60))
    base = datetime.combine(t0, time(hour=hours, minute=minutes), tzinfo=UTC)
    return base - timedelta(days=days_back)


def derive_patch_state(
    installed_kbs: list[str],
    t0: date,
    scan_source: str,
    rng: np.random.Generator,
) -> PatchState:
    """Construct a PatchState pydantic model from inputs."""
    return PatchState(
        kbs_installed=list(installed_kbs),
        last_scan=sample_scan_time(t0, rng),
        scan_source=scan_source,
    )
