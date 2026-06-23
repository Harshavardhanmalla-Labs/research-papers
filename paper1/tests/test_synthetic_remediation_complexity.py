"""Remediation complexity tests."""

from __future__ import annotations

from datetime import UTC, date, datetime

from paper1.audit.schema import (
    Host,
    PatchState,
    RemediationComplexityProfile,
    Vulnerability,
)
from paper1.synthetic.remediation_complexity import (
    HOST_MODIFIERS,
    compute_complexity,
)
from paper1.utils.seeds import make_rng


def _utc_dt() -> datetime:
    return datetime(2026, 5, 31, 12, 0, 0, tzinfo=UTC)


def _make_vuln() -> Vulnerability:
    return Vulnerability(
        cve_id="CVE-2025-0001",
        cpe_matches=["cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*"],
        cvss_v4_vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N",
        cvss_v4_base=9.3,
        cvss_version_used="v4",
        disclosure_date=date(2025, 4, 1),
        feed_fetch_timestamp=_utc_dt(),
    )


def _make_host(role: str, os_family: str = "windows_workstation") -> Host:
    return Host(
        host_id=f"H-{role}",
        os_family=os_family,
        os_version="v",
        role=role,
        network_zone="internal",
        identity_tier="tier_2",
        installed_software=[],
        patch_state=PatchState(kbs_installed=[], last_scan=_utc_dt(), scan_source="t"),
        last_seen_per_source={"inventory": _utc_dt()},
        group_id="G-1",
    )


def test_complexity_in_range():
    vuln = _make_vuln()
    host = _make_host("standard_workstation")
    profile = compute_complexity(vuln, host, {"category": "browser"}, make_rng(1))
    assert isinstance(profile, RemediationComplexityProfile)
    assert 0.0 <= profile.complexity_score <= 1.0


def test_domain_controller_higher_than_workstation_for_same_product():
    vuln = _make_vuln()
    meta = {"category": "database", "reboot_required_prior": 0.5}
    n = 30
    dc_scores = [
        compute_complexity(vuln, _make_host("domain_controller", "windows_server"), meta, make_rng(i)).complexity_score
        for i in range(n)
    ]
    wks_scores = [
        compute_complexity(vuln, _make_host("standard_workstation"), meta, make_rng(i)).complexity_score
        for i in range(n)
    ]
    assert sum(dc_scores) / n > sum(wks_scores) / n


def test_mobile_modifier_reduces_complexity():
    vuln = _make_vuln()
    meta = {"category": "mobile_os_component"}
    n = 30
    mobile_scores = [
        compute_complexity(vuln, _make_host("mobile_device", "ios"), meta, make_rng(i)).complexity_score
        for i in range(n)
    ]
    workstation_scores = [
        compute_complexity(vuln, _make_host("standard_workstation"), meta, make_rng(i)).complexity_score
        for i in range(n)
    ]
    assert sum(mobile_scores) / n < sum(workstation_scores) / n


def test_reboot_required_increases_complexity():
    vuln = _make_vuln()
    host = _make_host("standard_workstation")
    n = 100
    yes_meta = {"category": "browser", "reboot_required_prior": 1.0}
    no_meta = {"category": "browser", "reboot_required_prior": 0.0}
    yes = [compute_complexity(vuln, host, yes_meta, make_rng(i)).complexity_score for i in range(n)]
    no = [compute_complexity(vuln, host, no_meta, make_rng(i)).complexity_score for i in range(n)]
    assert sum(yes) / n > sum(no) / n


def test_complexity_validates_schema():
    vuln = _make_vuln()
    host = _make_host("standard_workstation")
    profile = compute_complexity(vuln, host, {"category": "browser"}, make_rng(1))
    assert profile.pair_id == f"{host.host_id}:{vuln.cve_id}"
    assert 0.0 <= profile.factor_reboot <= 1.0


def test_host_modifier_lookup():
    assert HOST_MODIFIERS["domain_controller"] > 0
    assert HOST_MODIFIERS["mobile_device"] < 0
