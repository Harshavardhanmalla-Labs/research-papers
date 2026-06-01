"""Feature assembly tests."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd
import pytest

from paper1.audit.schema import (
    AssetCriticalityProfile,
    ExploitSignal,
    LocalExposureProfile,
    RemediationComplexityProfile,
    Vulnerability,
)
from paper1.model.features import FEATURE_COLUMNS, build_feature_frame

T0 = date(2025, 6, 1)


def _utc() -> datetime:
    return datetime(2025, 6, 1, 0, 0, 0, tzinfo=UTC)


def _vuln(cve: str, *, base: float = 8.0, version: str = "v4", disclosure: date = date(2025, 1, 1)) -> Vulnerability:
    kwargs: dict = {
        "cve_id": cve,
        "cpe_matches": ["cpe:2.3:a:v:p:1.0:*:*:*:*:*:*:*"],
        "cvss_version_used": version,
        "disclosure_date": disclosure,
        "feed_fetch_timestamp": _utc(),
    }
    if version == "v4":
        kwargs["cvss_v4_vector"] = "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"
        kwargs["cvss_v4_base"] = base
    else:
        kwargs["cvss_v31_vector"] = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        kwargs["cvss_v31_base"] = base
    return Vulnerability(**kwargs)


def _signal(
    cve: str,
    *,
    epss: float = 0.5,
    kev: bool = False,
    due: date | None = None,
    kev_added: date | None = None,
) -> ExploitSignal:
    return ExploitSignal(
        cve_id=cve,
        epss_score=epss,
        epss_percentile=0.5,
        epss_fetch_timestamp=_utc(),
        epss_version="v4",
        kev_status=kev,
        kev_date_added=kev_added,
        kev_due_date=due,
        poc_observed=False,
        signal_staleness_days=0,
    )


def _crit(host: str, score: float = 0.6) -> AssetCriticalityProfile:
    return AssetCriticalityProfile(
        host_id=host,
        criticality_score=score,
        subscore_role=score,
        subscore_identity=score,
        subscore_network=score,
        subscore_data=score,
        derivation_method="t",
        identity_mapping_config="ad_entra_default",
        computed_at=_utc(),
    )


def _expo(pair_id: str, score: float = 0.7) -> LocalExposureProfile:
    return LocalExposureProfile(
        pair_id=pair_id,
        exposure_score=score,
        factor_installed_vuln=1.0,
        factor_service_running=1.0,
        factor_network_reachable=score,
        factor_mitigation_present=0.0,
        factor_auth_precondition_met=1.0,
        reachability_assumption="zone=dmz",
        evaluator_version="t",
    )


def _cmplx(pair_id: str, score: float = 0.4) -> RemediationComplexityProfile:
    return RemediationComplexityProfile(
        pair_id=pair_id,
        complexity_score=score,
        factor_reboot=0.0,
        factor_user_disruption=score,
        factor_service_dep=score,
        factor_regression=score,
        factor_channel=1.0,
        factor_bundle=1.0,
        host_modifier=0.0,
    )


def _pairs(cves_hosts: list[tuple[str, str]]) -> pd.DataFrame:
    rows = [
        {"pair_id": f"{h}:{c}", "cve_id": c, "host_id": h} for c, h in cves_hosts
    ]
    return pd.DataFrame(rows)


def test_feature_frame_builds():
    pairs = _pairs([("CVE-2024-0001", "H-1")])
    ff = build_feature_frame(
        pairs,
        [_vuln("CVE-2024-0001", base=8.0)],
        [_signal("CVE-2024-0001", epss=0.5)],
        [_crit("H-1", 0.6)],
        [_expo("H-1:CVE-2024-0001", 0.7)],
        [_cmplx("H-1:CVE-2024-0001", 0.4)],
        T0,
    )
    assert set(FEATURE_COLUMNS) <= set(ff.columns)
    row = ff.iloc[0]
    assert row["S"] == pytest.approx(0.8)  # 8.0 / 10
    assert row["E"] == pytest.approx(0.5)
    assert row["K"] == 0.0
    assert row["C"] == pytest.approx(0.6)
    assert row["X"] == pytest.approx(0.7)
    assert row["R"] == pytest.approx(0.4)


def test_s_normalized_by_ten():
    pairs = _pairs([("CVE-2024-0002", "H-1")])
    ff = build_feature_frame(
        pairs, [_vuln("CVE-2024-0002", base=9.3)], [_signal("CVE-2024-0002")],
        [_crit("H-1")], [_expo("H-1:CVE-2024-0002")], [_cmplx("H-1:CVE-2024-0002")], T0,
    )
    assert ff.iloc[0]["S"] == pytest.approx(0.93)


def test_u_is_one_for_overdue_kev():
    pairs = _pairs([("CVE-2024-0003", "H-1")])
    ff = build_feature_frame(
        pairs,
        [_vuln("CVE-2024-0003")],
        [_signal("CVE-2024-0003", kev=True, due=date(2025, 5, 1))],  # before t0
        [_crit("H-1")],
        [_expo("H-1:CVE-2024-0003")],
        [_cmplx("H-1:CVE-2024-0003")],
        T0,
    )
    assert ff.iloc[0]["U"] == pytest.approx(1.0)


def test_u_from_due_date_within_30_days():
    pairs = _pairs([("CVE-2024-0004", "H-1")])
    ff = build_feature_frame(
        pairs,
        [_vuln("CVE-2024-0004")],
        [_signal("CVE-2024-0004", kev=True, due=date(2025, 6, 16))],  # +15 days
        [_crit("H-1")],
        [_expo("H-1:CVE-2024-0004")],
        [_cmplx("H-1:CVE-2024-0004")],
        T0,
    )
    # U = 1 - 15/30 = 0.5
    assert ff.iloc[0]["U"] == pytest.approx(0.5)


def test_u_computed_from_e_k_when_no_due_date():
    pairs = _pairs([("CVE-2024-0005", "H-1")])
    ff = build_feature_frame(
        pairs,
        [_vuln("CVE-2024-0005")],
        [_signal("CVE-2024-0005", epss=0.4, kev=False)],
        [_crit("H-1")],
        [_expo("H-1:CVE-2024-0005")],
        [_cmplx("H-1:CVE-2024-0005")],
        T0,
    )
    # U = 0.25*0 + 0.75*0.4 = 0.3
    assert ff.iloc[0]["U"] == pytest.approx(0.3)


def test_missing_e_imputed_median():
    triples = [("CVE-2024-7001", "H-1"), ("CVE-2024-7002", "H-2"), ("CVE-2024-7003", "H-3")]
    pairs = _pairs(triples)
    vulns = [_vuln(c) for c, _ in triples]
    # Signals only for two CVEs; CVE-2024-7003 missing -> E imputed.
    signals = [_signal("CVE-2024-7001", epss=0.2), _signal("CVE-2024-7002", epss=0.8)]
    crit = [_crit("H-1"), _crit("H-2"), _crit("H-3")]
    expo = [_expo(f"{h}:{c}") for c, h in triples]
    cmplx = [_cmplx(f"{h}:{c}") for c, h in triples]
    ff = build_feature_frame(pairs, vulns, signals, crit, expo, cmplx, T0, imputation_strategy="median")
    missing_row = ff[ff["cve_id"] == "CVE-2024-7003"].iloc[0]
    assert missing_row["E"] == pytest.approx(0.5)  # median of {0.2, 0.8}
    assert "E" in missing_row["imputed_features"]
    assert bool(missing_row["feature_imputed"]) is True


def test_missing_s_imputed_zero_with_zero_strategy():
    pairs = _pairs([("CVE-2024-0006", "H-1")])
    # Vulnerability with no CVSS base -> S missing. Use v4 with base provided
    # but for missing we simply omit the vuln from the list.
    ff = build_feature_frame(
        pairs,
        [],  # no vulnerabilities -> S missing
        [_signal("CVE-2024-0006", epss=0.3)],
        [_crit("H-1")],
        [_expo("H-1:CVE-2024-0006")],
        [_cmplx("H-1:CVE-2024-0006")],
        T0,
        imputation_strategy="zero",
    )
    assert ff.iloc[0]["S"] == 0.0
    assert "S" in ff.iloc[0]["imputed_features"]


def test_missing_kev_defaults_zero_with_warning():
    pairs = _pairs([("CVE-2024-0007", "H-1")])
    ff = build_feature_frame(
        pairs,
        [_vuln("CVE-2024-0007")],
        [],  # no signal -> K missing, E missing
        [_crit("H-1")],
        [_expo("H-1:CVE-2024-0007")],
        [_cmplx("H-1:CVE-2024-0007")],
        T0,
        imputation_strategy="zero",
    )
    assert ff.iloc[0]["K"] == 0.0
    assert any("K_missing" in w for w in ff.iloc[0]["feature_warnings"])


def test_values_clipped_to_unit_interval():
    pairs = _pairs([("CVE-2024-0008", "H-1")])
    ff = build_feature_frame(
        pairs,
        [_vuln("CVE-2024-0008", base=10.0)],
        [_signal("CVE-2024-0008", epss=1.0)],
        [_crit("H-1", 1.0)],
        [_expo("H-1:CVE-2024-0008", 1.0)],
        [_cmplx("H-1:CVE-2024-0008", 1.0)],
        T0,
    )
    for f in FEATURE_COLUMNS:
        assert 0.0 <= ff.iloc[0][f] <= 1.0


def test_duplicate_pair_id_raises():
    pairs = pd.DataFrame(
        {"pair_id": ["P", "P"], "cve_id": ["CVE-2024-0009", "CVE-2024-0009"], "host_id": ["H", "H"]}
    )
    with pytest.raises(ValueError):
        build_feature_frame(pairs, [], [], [], [], [], T0)


def test_missing_pair_id_column_raises():
    pairs = pd.DataFrame({"cve_id": ["CVE-2024-0010"], "host_id": ["H"]})
    with pytest.raises(ValueError):
        build_feature_frame(pairs, [], [], [], [], [], T0)


def test_output_preserves_pair_order():
    pairs = _pairs([("CVE-2024-9001", "H-9"), ("CVE-2024-1002", "H-1")])
    vulns = [_vuln("CVE-2024-9001"), _vuln("CVE-2024-1002")]
    signals = [_signal("CVE-2024-9001"), _signal("CVE-2024-1002")]
    crit = [_crit("H-9"), _crit("H-1")]
    expo = [_expo("H-9:CVE-2024-9001"), _expo("H-1:CVE-2024-1002")]
    cmplx = [_cmplx("H-9:CVE-2024-9001"), _cmplx("H-1:CVE-2024-1002")]
    ff = build_feature_frame(pairs, vulns, signals, crit, expo, cmplx, T0)
    # Input order (H-9 first) is preserved, NOT sorted.
    assert ff["pair_id"].tolist() == ["H-9:CVE-2024-9001", "H-1:CVE-2024-1002"]


def test_kev_future_addition_raises_leakage():
    pairs = _pairs([("CVE-2024-0011", "H-1")])
    with pytest.raises(ValueError):
        build_feature_frame(
            pairs,
            [_vuln("CVE-2024-0011")],
            [_signal("CVE-2024-0011", kev=True, kev_added=date(2025, 7, 1))],  # > t0
            [_crit("H-1")],
            [_expo("H-1:CVE-2024-0011")],
            [_cmplx("H-1:CVE-2024-0011")],
            T0,
        )


def test_future_disclosure_raises_leakage():
    pairs = _pairs([("CVE-2026-0012", "H-1")])
    with pytest.raises(ValueError):
        build_feature_frame(
            pairs,
            [_vuln("CVE-2026-0012", disclosure=date(2026, 1, 1))],
            [_signal("CVE-2026-0012")],
            [_crit("H-1")],
            [_expo("H-1:CVE-2026-0012")],
            [_cmplx("H-1:CVE-2026-0012")],
            T0,
        )


def test_unsupported_imputation_raises():
    pairs = _pairs([("CVE-2024-0013", "H-1")])
    with pytest.raises(NotImplementedError):
        build_feature_frame(
            pairs, [_vuln("CVE-2024-0013")], [_signal("CVE-2024-0013")],
            [_crit("H-1")], [_expo("H-1:CVE-2024-0013")], [_cmplx("H-1:CVE-2024-0013")],
            T0, imputation_strategy="last_known",
        )


def test_v31_fallback_for_s():
    pairs = _pairs([("CVE-2024-0014", "H-1")])
    ff = build_feature_frame(
        pairs,
        [_vuln("CVE-2024-0014", base=6.0, version="v31")],
        [_signal("CVE-2024-0014")],
        [_crit("H-1")],
        [_expo("H-1:CVE-2024-0014")],
        [_cmplx("H-1:CVE-2024-0014")],
        T0,
    )
    assert ff.iloc[0]["S"] == pytest.approx(0.6)
