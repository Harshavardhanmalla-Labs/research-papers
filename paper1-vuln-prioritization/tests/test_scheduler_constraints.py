"""Scheduler constraint predicate tests."""

from __future__ import annotations

from paper1.scheduler.constraints import (
    all_constraints_satisfied,
    check_dependency,
    check_domain_controller_staging,
    check_group_cap,
    dc_first_succeeded,
    dependency_satisfied,
    group_cap_violated,
)


def _row(pair_id="H-1:CVE-2024-0001", **kw):
    base = {
        "pair_id": pair_id,
        "cve_id": "CVE-2024-0001",
        "host_id": "H-1",
        "host_role": "member_server",
        "group_id": None,
        "dependency_group": None,
    }
    base.update(kw)
    return base


# -----------------------------------------------------------------------
# group caps
# -----------------------------------------------------------------------


def test_group_cap_blocks_when_reached():
    scheduled = [_row("H-1:c", group_id="G1"), _row("H-2:c", group_id="G1")]
    pair = _row("H-3:c", group_id="G1")
    res = check_group_cap(scheduled, pair, {"G1": 2})
    assert not res.allowed
    assert res.reason == "GROUP_CAP_REACHED"
    assert group_cap_violated(scheduled, pair, {"G1": 2})


def test_group_cap_allows_below_cap():
    scheduled = [_row("H-1:c", group_id="G1")]
    pair = _row("H-2:c", group_id="G1")
    assert check_group_cap(scheduled, pair, {"G1": 3}).allowed


def test_group_cap_fallback_to_host_role():
    scheduled = [_row("H-1:c", group_id=None, host_role="kiosk")]
    pair = _row("H-2:c", group_id=None, host_role="kiosk")
    res = check_group_cap(scheduled, pair, {"kiosk": 1})
    assert not res.allowed


def test_group_cap_none_config_allows():
    assert check_group_cap([], _row(), None).allowed


# -----------------------------------------------------------------------
# dependency
# -----------------------------------------------------------------------


def test_dependency_satisfied_when_ready():
    pair = _row(dependency_group="D1")
    assert dependency_satisfied(pair, [], {"D1": True})


def test_dependency_pending_blocks():
    pair = _row(dependency_group="D1")
    res = check_dependency(pair, [], {"D1": False})
    assert not res.allowed
    assert res.reason == "DEPENDENCY_PENDING"


def test_dependency_none_allowed():
    assert dependency_satisfied(_row(dependency_group=None), [])


def test_dependency_missing_state_allows_with_warning():
    pair = _row(dependency_group="D1")
    res = check_dependency(pair, [], None)
    assert res.allowed
    assert res.details.get("warning") == "dependency_state_missing"


# -----------------------------------------------------------------------
# domain-controller staging
# -----------------------------------------------------------------------


def test_first_dc_allowed():
    pair = _row(host_role="domain_controller", group_id="DCG")
    res = check_domain_controller_staging(pair, [], {})
    assert res.allowed


def test_second_dc_blocked_until_first_success():
    scheduled = [_row("H-1:c", host_role="domain_controller", group_id="DCG")]
    pair = _row("H-2:c", host_role="domain_controller", group_id="DCG")
    res = check_domain_controller_staging(pair, scheduled, {})
    assert not res.allowed
    assert res.reason == "DC_STAGED_ROLLOUT_AWAIT_FIRST"


def test_second_dc_allowed_after_first_success():
    scheduled = [_row("H-1:c", host_role="domain_controller", group_id="DCG")]
    pair = _row("H-2:c", host_role="domain_controller", group_id="DCG")
    res = check_domain_controller_staging(pair, scheduled, {"DCG": True})
    assert res.allowed


def test_dc_first_succeeded_helper():
    pair = _row(host_role="domain_controller", group_id="DCG")
    assert not dc_first_succeeded(pair, {})
    assert dc_first_succeeded(pair, {"DCG": True})


def test_non_dc_role_allowed():
    res = check_domain_controller_staging(_row(host_role="kiosk"), [], {})
    assert res.allowed


# -----------------------------------------------------------------------
# combined
# -----------------------------------------------------------------------


def test_all_constraints_first_failure_wins():
    scheduled = [_row("H-1:c", group_id="G1")]
    pair = _row("H-2:c", group_id="G1", dependency_group="D1")
    res = all_constraints_satisfied(pair, scheduled, {"G1": 1}, {"D1": False}, {})
    # group cap fails first
    assert not res.allowed
    assert res.reason == "GROUP_CAP_REACHED"


def test_all_constraints_allowed():
    assert all_constraints_satisfied(_row(), [], None, None, None).allowed
