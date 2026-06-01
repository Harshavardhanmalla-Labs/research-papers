"""Schema validation tests."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from paper1.audit.schema import (
    AssetCriticalityProfile,
    AuditDecisionRecord,
    ExperimentConfig,
    ExploitSignal,
    Host,
    InstalledSoftware,
    LocalExposureProfile,
    PatchState,
    RemediationComplexityProfile,
    Vulnerability,
    VulnerabilityHostPair,
)

# ---------------------------------------------------------------------------
# Vulnerability
# ---------------------------------------------------------------------------


def _valid_vuln_kwargs(utc_dt: datetime) -> dict:
    return {
        "cve_id": "CVE-2025-12345",
        "cwe_ids": ["CWE-79"],
        "cpe_matches": ["cpe:2.3:a:vendor:product:1.2:*:*:*:*:*:*:*"],
        "cvss_v4_vector": "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N",
        "cvss_v4_base": 9.3,
        "cvss_version_used": "v4",
        "disclosure_date": date(2025, 4, 8),
        "feed_fetch_timestamp": utc_dt,
    }


def test_valid_vulnerability(utc_dt):
    v = Vulnerability(**_valid_vuln_kwargs(utc_dt))
    assert v.cve_id == "CVE-2025-12345"
    assert v.cvss_v4_base == 9.3


def test_invalid_cve_id_fails(utc_dt):
    kwargs = _valid_vuln_kwargs(utc_dt)
    kwargs["cve_id"] = "BAD-2025-1"
    with pytest.raises(ValidationError):
        Vulnerability(**kwargs)


def test_cvss_out_of_range_fails(utc_dt):
    kwargs = _valid_vuln_kwargs(utc_dt)
    kwargs["cvss_v4_base"] = 11.0
    with pytest.raises(ValidationError):
        Vulnerability(**kwargs)


def test_naive_datetime_fails():
    kwargs = _valid_vuln_kwargs(datetime(2026, 5, 26, 12, 0, 0))  # naive
    with pytest.raises(ValidationError):
        Vulnerability(**kwargs)


def test_non_utc_timezone_fails(utc_dt):
    kwargs = _valid_vuln_kwargs(utc_dt)
    kwargs["feed_fetch_timestamp"] = datetime(
        2026, 5, 26, 12, 0, 0, tzinfo=timezone(timedelta(hours=5))
    )
    with pytest.raises(ValidationError):
        Vulnerability(**kwargs)


def test_cvss_version_mismatch_fails(utc_dt):
    kwargs = _valid_vuln_kwargs(utc_dt)
    kwargs["cvss_version_used"] = "v31"
    # v31 fields are None
    with pytest.raises(ValidationError):
        Vulnerability(**kwargs)


def test_extra_field_fails(utc_dt):
    kwargs = _valid_vuln_kwargs(utc_dt)
    kwargs["unexpected_extra_field"] = "not allowed"
    with pytest.raises(ValidationError):
        Vulnerability(**kwargs)


def test_frozen_model_cannot_be_mutated(utc_dt):
    v = Vulnerability(**_valid_vuln_kwargs(utc_dt))
    with pytest.raises((ValidationError, AttributeError, TypeError)):
        v.cve_id = "CVE-2024-99999"


# ---------------------------------------------------------------------------
# Host
# ---------------------------------------------------------------------------


def _valid_host_kwargs(utc_dt: datetime) -> dict:
    return {
        "host_id": "H-test-001",
        "os_family": "windows_workstation",
        "os_version": "Windows 11 23H2 22631.3593",
        "role": "standard_workstation",
        "network_zone": "internal",
        "identity_tier": "tier_2",
        "data_sensitivity_proxy": "general",
        "installed_software": [
            InstalledSoftware(
                cpe="cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*",
                product="product",
                vendor="vendor",
                version="1.0",
            )
        ],
        "patch_state": PatchState(
            kbs_installed=["KB5036893"],
            last_scan=utc_dt,
            scan_source="sccm",
        ),
        "last_seen_per_source": {"sccm": utc_dt, "tanium": utc_dt},
        "group_id": "G-1",
    }


def test_valid_host(utc_dt):
    h = Host(**_valid_host_kwargs(utc_dt))
    assert h.host_id == "H-test-001"


def test_host_naive_last_seen_fails(utc_dt):
    kwargs = _valid_host_kwargs(utc_dt)
    kwargs["last_seen_per_source"] = {"sccm": datetime(2026, 5, 26, 12, 0, 0)}
    with pytest.raises(ValidationError):
        Host(**kwargs)


# ---------------------------------------------------------------------------
# Pair
# ---------------------------------------------------------------------------


def test_valid_pair(utc_dt):
    p = VulnerabilityHostPair(
        pair_id="H-test-001:CVE-2025-12345",
        cve_id="CVE-2025-12345",
        host_id="H-test-001",
        match_method="cpe_exact",
        match_confidence=0.95,
        pair_status="open",
        first_observed=utc_dt,
    )
    assert p.match_confidence == 0.95


def test_pair_invalid_status_fails(utc_dt):
    with pytest.raises(ValidationError):
        VulnerabilityHostPair(
            pair_id="X",
            cve_id="CVE-2025-12345",
            host_id="H-1",
            match_method="cpe_exact",
            match_confidence=0.5,
            pair_status="not_a_real_status",
            first_observed=utc_dt,
        )


def test_pair_confidence_out_of_range_fails(utc_dt):
    with pytest.raises(ValidationError):
        VulnerabilityHostPair(
            pair_id="X",
            cve_id="CVE-2025-12345",
            host_id="H-1",
            match_method="cpe_exact",
            match_confidence=1.5,
            pair_status="open",
            first_observed=utc_dt,
        )


# ---------------------------------------------------------------------------
# ExploitSignal
# ---------------------------------------------------------------------------


def test_valid_exploit_signal(utc_dt):
    e = ExploitSignal(
        cve_id="CVE-2025-12345",
        epss_score=0.873,
        epss_percentile=0.991,
        epss_fetch_timestamp=utc_dt,
        epss_version="v4",
        kev_status=True,
        kev_date_added=date(2026, 4, 15),
        kev_due_date=date(2026, 5, 6),
        poc_observed=True,
        poc_first_seen=utc_dt,
        signal_staleness_days=0,
    )
    assert e.kev_status


# ---------------------------------------------------------------------------
# AssetCriticality, LocalExposure, RemediationComplexity
# ---------------------------------------------------------------------------


def test_criticality_subscores_in_range(utc_dt):
    ac = AssetCriticalityProfile(
        host_id="H-1",
        criticality_score=0.81,
        subscore_role=0.90,
        subscore_identity=1.00,
        subscore_network=0.70,
        subscore_data=0.85,
        derivation_method="acr_v0.3",
        identity_mapping_config="ad_entra_default",
        computed_at=utc_dt,
    )
    assert ac.criticality_score == 0.81


def test_criticality_subscore_out_of_range_fails(utc_dt):
    with pytest.raises(ValidationError):
        AssetCriticalityProfile(
            host_id="H-1",
            criticality_score=0.81,
            subscore_role=1.5,  # out of range
            subscore_identity=1.00,
            subscore_network=0.70,
            subscore_data=0.85,
            derivation_method="acr_v0.3",
            identity_mapping_config="ad_entra_default",
            computed_at=utc_dt,
        )


def test_local_exposure_valid():
    lep = LocalExposureProfile(
        pair_id="H-1:CVE-2025-12345",
        exposure_score=0.75,
        factor_installed_vuln=1.0,
        factor_service_running=1.0,
        factor_network_reachable=1.0,
        factor_mitigation_present=0.0,
        factor_auth_precondition_met=1.0,
        reachability_assumption="zone_default",
        evaluator_version="lee_v0.2",
    )
    assert lep.exposure_score == 0.75


def test_remediation_complexity_valid():
    rcp = RemediationComplexityProfile(
        pair_id="H-1:CVE-2025-12345",
        complexity_score=0.55,
        factor_reboot=1.0,
        factor_user_disruption=0.3,
        factor_service_dep=0.5,
        factor_regression=0.4,
        factor_channel=1.0,
        factor_bundle=1.0,
        host_modifier=0.0,
    )
    assert rcp.complexity_score == 0.55


# ---------------------------------------------------------------------------
# AuditDecisionRecord
# ---------------------------------------------------------------------------


def _add_hashes(kwargs: dict) -> dict:
    h = "0" * 64
    return {**kwargs, "record_hash": h, "prior_record_hash": h}


def test_score_record_requires_features(sample_score_kwargs):
    kwargs = dict(sample_score_kwargs)
    kwargs.pop("feature_values")
    with pytest.raises(ValidationError):
        AuditDecisionRecord(**_add_hashes(kwargs))


def test_score_record_requires_contributions(sample_score_kwargs):
    kwargs = dict(sample_score_kwargs)
    kwargs.pop("feature_contributions")
    with pytest.raises(ValidationError):
        AuditDecisionRecord(**_add_hashes(kwargs))


def test_accept_risk_record_requires_reason(sample_accept_risk_kwargs):
    kwargs = dict(sample_accept_risk_kwargs)
    kwargs.pop("risk_acceptance_reason")
    with pytest.raises(ValidationError):
        AuditDecisionRecord(**_add_hashes(kwargs))


def test_accept_risk_record_requires_approver(sample_accept_risk_kwargs):
    kwargs = dict(sample_accept_risk_kwargs)
    kwargs.pop("risk_acceptance_approver_id")
    with pytest.raises(ValidationError):
        AuditDecisionRecord(**_add_hashes(kwargs))


def test_accept_risk_record_requires_expiration(sample_accept_risk_kwargs):
    kwargs = dict(sample_accept_risk_kwargs)
    kwargs.pop("risk_acceptance_expiration_date")
    with pytest.raises(ValidationError):
        AuditDecisionRecord(**_add_hashes(kwargs))


def test_record_hash_must_be_hex(sample_score_kwargs):
    bad = dict(sample_score_kwargs, record_hash="NOTAHEX", prior_record_hash="0" * 64)
    with pytest.raises(ValidationError):
        AuditDecisionRecord(**bad)


def test_record_hash_wrong_length(sample_score_kwargs):
    bad = dict(sample_score_kwargs, record_hash="ab" * 30, prior_record_hash="0" * 64)
    with pytest.raises(ValidationError):
        AuditDecisionRecord(**bad)


def test_audit_record_extra_field_fails(sample_score_kwargs):
    bad = dict(sample_score_kwargs)
    bad["unexpected"] = "x"
    with pytest.raises(ValidationError):
        AuditDecisionRecord(**_add_hashes(bad))


def test_audit_record_frozen(sample_score_kwargs):
    r = AuditDecisionRecord(**_add_hashes(sample_score_kwargs))
    with pytest.raises((ValidationError, AttributeError, TypeError)):
        r.record_id = "tampered"


# ---------------------------------------------------------------------------
# ExperimentConfig
# ---------------------------------------------------------------------------


def test_experiment_config_window_order_enforced():
    with pytest.raises(ValidationError):
        ExperimentConfig(
            config_name="x",
            seed_master=1,
            fleet_size=10,
            capacity_ratio=0.01,
            label="A",
            approver_policy="A",
            identity_config="ad_entra_default",
            blackout_config="primary",
            epss_version_handling="pooled_with_covariate",
            data_window_start=date(2026, 5, 31),
            data_window_end=date(2024, 6, 1),  # end before start
            H_days=30,
            train_split_months=18,
            strategies=["random"],
            seed_count=1,
            maintenance_cadence_days=14,
            remediation_failure_rate=0.05,
            rollback_probability_given_failure=0.3,
            output_dir="results/x",
        )
