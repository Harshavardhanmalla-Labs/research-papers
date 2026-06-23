"""Blackout-window evaluation.

All times are UTC. For Phase 8 a configured ``local`` timezone is treated
as UTC (documented approximation). Domain-controller staged rollout is a
*constraint* (see constraints.py), not a blackout, and is not handled
here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

__all__ = [
    "BlackoutDecision",
    "blackout_active",
    "is_business_hours",
    "is_cab_blackout",
    "is_first_saturday_maintenance",
    "is_in_maintenance_window",
    "load_blackout_config",
]

_WEEKDAY = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
_DEFAULT_BUSINESS_WEEKDAYS = (0, 1, 2, 3, 4)


@dataclass(frozen=True)
class BlackoutDecision:
    blocked: bool
    reason: str | None = None
    override_applied: bool = False
    details: dict[str, Any] = field(default_factory=dict)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_blackout_config(path_or_name: str | Path) -> dict[str, Any]:
    """Load a blackout config by file path or by short name (e.g. 'primary')."""
    import yaml

    p = Path(path_or_name)
    if not p.exists():
        name = str(path_or_name)
        p = _repo_root() / "configs" / f"blackout_{name}.yaml"
    if not p.exists():
        raise FileNotFoundError(f"blackout config not found: {path_or_name}")
    with open(p, encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    if not isinstance(config, dict) or "blackouts" not in config:
        raise ValueError(f"invalid blackout config: {p}")
    return config


def _in_hours(hour: int, hours: tuple[int, int] | list[int]) -> bool:
    h0, h1 = int(hours[0]), int(hours[1])
    if h0 <= h1:
        return h0 <= hour < h1
    # Wraps past midnight (e.g., 22..02): same-day approximation.
    return hour >= h0 or hour < h1


def _weekdays_to_ints(weekdays: Any) -> set[int]:
    if weekdays is None:
        return set(_DEFAULT_BUSINESS_WEEKDAYS)
    out: set[int] = set()
    for w in weekdays:
        if isinstance(w, int):
            out.add(w)
        else:
            out.add(_WEEKDAY[str(w).lower()[:3]])
    return out


def is_business_hours(
    dt: datetime,
    hours: tuple[int, int] = (8, 18),
    weekdays: Any = None,
) -> bool:
    wd = _weekdays_to_ints(weekdays) if weekdays is not None else set(_DEFAULT_BUSINESS_WEEKDAYS)
    return dt.weekday() in wd and _in_hours(dt.hour, hours)


def is_in_maintenance_window(dt: datetime, weekday: str, hours: tuple[int, int]) -> bool:
    target = _WEEKDAY[str(weekday).lower()[:3]]
    return dt.weekday() == target and _in_hours(dt.hour, hours)


def is_cab_blackout(dt: datetime, weekday: str) -> bool:
    return dt.weekday() == _WEEKDAY[str(weekday).lower()[:3]]


def is_first_saturday_maintenance(dt: datetime, hours: tuple[int, int] = (22, 2)) -> bool:
    """First-Saturday-of-month maintenance window (same-day approximation)."""
    return dt.weekday() == _WEEKDAY["sat"] and dt.day <= 7 and _in_hours(dt.hour, hours)


def _parse_due(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _kev_override_active(pair_row: Mapping[str, Any], now: datetime, hours: int) -> bool:
    due = _parse_due(pair_row.get("kev_due_date"))
    if due is None:
        return False
    deadline = datetime.combine(due, datetime.max.time(), tzinfo=now.tzinfo)
    return deadline <= now + timedelta(hours=hours)


def blackout_active(
    pair_row: Mapping[str, Any],
    blackout_config: Mapping[str, Any],
    now: datetime,
) -> BlackoutDecision:
    """Decide whether `pair_row` is in a blackout at time `now` (UTC)."""
    role = pair_row.get("host_role")
    rules = (blackout_config.get("blackouts") or {})
    rule = rules.get(role)
    if rule is None:
        return BlackoutDecision(False, None, False, {"warning": f"no_blackout_rule_for_role:{role}"})

    # First-Saturday strict-monthly maintenance: allowed only inside window.
    if "first_saturday_maintenance" in rule:
        hours = tuple(rule["first_saturday_maintenance"].get("hours", [22, 2]))
        if is_first_saturday_maintenance(now, hours):
            return BlackoutDecision(False, None, False, {"window": "first_saturday"})
        # public-facing KEV override still applies even under strict monthly.
        if role == "public_facing_server" and "kev_override_hours" in rule and _kev_override_active(
            pair_row, now, int(rule["kev_override_hours"])
        ):
            return BlackoutDecision(False, "KEV_OVERRIDE", True, {"window": "first_saturday"})
        return BlackoutDecision(True, "OUTSIDE_FIRST_SATURDAY_MAINTENANCE", False, {})

    # Weekly maintenance window: allowed only inside.
    if "maintenance_window" in rule:
        mw = rule["maintenance_window"]
        if is_in_maintenance_window(now, mw["weekday"], tuple(mw["hours"])):
            return BlackoutDecision(False, None, False, {"window": "maintenance"})
        return BlackoutDecision(True, "RESTRICTED_OUTSIDE_MAINTENANCE", False, {})

    # CAB blackout weekday: blocked all that day.
    if "cab_blackout_weekday" in rule:
        if is_cab_blackout(now, rule["cab_blackout_weekday"]):
            return BlackoutDecision(True, "CAB_BLACKOUT", False, {"weekday": rule["cab_blackout_weekday"]})
        return BlackoutDecision(False, None, False, {})

    # Business-hours blackout (kiosk, public-facing).
    if "business_hours" in rule:
        bh = rule["business_hours"]
        hours = tuple(bh.get("hours", [8, 18]))
        weekdays = bh.get("weekdays")
        if is_business_hours(now, hours, weekdays):
            if "kev_override_hours" in bh and _kev_override_active(
                pair_row, now, int(bh["kev_override_hours"])
            ):
                return BlackoutDecision(False, "KEV_OVERRIDE", True, {"window": "business_hours"})
            label = "PUBLIC_FACING_BUSINESS_HOURS" if role == "public_facing_server" else "KIOSK_BUSINESS_HOURS"
            return BlackoutDecision(True, label, False, {"window": "business_hours"})
        return BlackoutDecision(False, None, False, {})

    # Rule present but no recognized window type (e.g., DC staged_rollout only).
    return BlackoutDecision(False, None, False, {"note": "no_time_window_rule"})
