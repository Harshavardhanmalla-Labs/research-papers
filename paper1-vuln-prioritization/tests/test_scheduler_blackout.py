"""Blackout-window tests (all times UTC)."""

from __future__ import annotations

from datetime import UTC, date, datetime

from paper1.scheduler.blackout import (
    blackout_active,
    is_business_hours,
    is_cab_blackout,
    is_first_saturday_maintenance,
    is_in_maintenance_window,
    load_blackout_config,
)

# 2025-06-10 is a Tuesday; 2025-06-07 a (first) Saturday; 2025-06-11 a Wednesday;
# 2025-06-14 a (second) Saturday.
TUE_BUSINESS = datetime(2025, 6, 10, 10, 0, tzinfo=UTC)
TUE_EVENING = datetime(2025, 6, 10, 20, 0, tzinfo=UTC)
SAT_FIRST_NIGHT = datetime(2025, 6, 7, 23, 0, tzinfo=UTC)
SAT_FIRST_DAY = datetime(2025, 6, 7, 10, 0, tzinfo=UTC)
SAT_SECOND_NIGHT = datetime(2025, 6, 14, 23, 0, tzinfo=UTC)
WED = datetime(2025, 6, 11, 10, 0, tzinfo=UTC)

PRIMARY = load_blackout_config("primary")
STRICT = load_blackout_config("strict_monthly")


def _row(role, **kw):
    base = {"pair_id": "H:CVE-2024-0001", "cve_id": "CVE-2024-0001", "host_id": "H", "host_role": role}
    base.update(kw)
    return base


# -----------------------------------------------------------------------
# helpers
# -----------------------------------------------------------------------


def test_is_business_hours_weekday():
    assert is_business_hours(TUE_BUSINESS)
    assert not is_business_hours(TUE_EVENING)
    assert not is_business_hours(SAT_FIRST_DAY)  # weekend


def test_is_cab_blackout():
    assert is_cab_blackout(WED, "wed")
    assert not is_cab_blackout(TUE_BUSINESS, "wed")


def test_is_in_maintenance_window_wrap():
    assert is_in_maintenance_window(SAT_FIRST_NIGHT, "sat", (22, 2))
    assert not is_in_maintenance_window(TUE_BUSINESS, "sat", (22, 2))


def test_is_first_saturday_maintenance():
    assert is_first_saturday_maintenance(SAT_FIRST_NIGHT, (22, 2))
    assert not is_first_saturday_maintenance(SAT_SECOND_NIGHT, (22, 2))
    assert not is_first_saturday_maintenance(TUE_BUSINESS, (22, 2))


# -----------------------------------------------------------------------
# kiosk
# -----------------------------------------------------------------------


def test_kiosk_blocked_during_business_hours():
    d = blackout_active(_row("kiosk"), PRIMARY, TUE_BUSINESS)
    assert d.blocked
    assert d.reason == "KIOSK_BUSINESS_HOURS"


def test_kiosk_allowed_after_hours():
    assert not blackout_active(_row("kiosk"), PRIMARY, TUE_EVENING).blocked


# -----------------------------------------------------------------------
# public-facing
# -----------------------------------------------------------------------


def test_public_facing_blocked_during_business_hours():
    d = blackout_active(_row("public_facing_server"), PRIMARY, TUE_BUSINESS)
    assert d.blocked
    assert d.reason == "PUBLIC_FACING_BUSINESS_HOURS"


def test_public_facing_kev_override_applies():
    row = _row("public_facing_server", kev_due_date=date(2025, 6, 10))  # due today
    d = blackout_active(row, PRIMARY, TUE_BUSINESS)
    assert not d.blocked
    assert d.override_applied


# -----------------------------------------------------------------------
# member server CAB
# -----------------------------------------------------------------------


def test_member_server_cab_blocks_on_wednesday():
    d = blackout_active(_row("member_server"), PRIMARY, WED)
    assert d.blocked
    assert d.reason == "CAB_BLACKOUT"


def test_member_server_allowed_other_day():
    assert not blackout_active(_row("member_server"), PRIMARY, TUE_BUSINESS).blocked


# -----------------------------------------------------------------------
# restricted zone
# -----------------------------------------------------------------------


def test_restricted_zone_allowed_only_in_window():
    assert not blackout_active(_row("restricted_zone_system"), PRIMARY, SAT_FIRST_NIGHT).blocked
    d = blackout_active(_row("restricted_zone_system"), PRIMARY, TUE_BUSINESS)
    assert d.blocked
    assert d.reason == "RESTRICTED_OUTSIDE_MAINTENANCE"


# -----------------------------------------------------------------------
# unknown role
# -----------------------------------------------------------------------


def test_unknown_role_not_blocked_with_warning():
    d = blackout_active(_row("weird_role"), PRIMARY, TUE_BUSINESS)
    assert not d.blocked
    assert "warning" in d.details


# -----------------------------------------------------------------------
# strict monthly
# -----------------------------------------------------------------------


def test_strict_monthly_allowed_first_saturday_window():
    assert not blackout_active(_row("kiosk"), STRICT, SAT_FIRST_NIGHT).blocked


def test_strict_monthly_blocked_second_saturday():
    d = blackout_active(_row("kiosk"), STRICT, SAT_SECOND_NIGHT)
    assert d.blocked
    assert d.reason == "OUTSIDE_FIRST_SATURDAY_MAINTENANCE"


def test_strict_monthly_blocked_weekday():
    assert blackout_active(_row("kiosk"), STRICT, TUE_BUSINESS).blocked
