"""Asset criticality + IPES tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, time

import pytest

from paper1.audit.schema import AssetCriticalityProfile
from paper1.synthetic.catalogs import load_host_type_defaults
from paper1.synthetic.criticality import (
    compute_criticality,
    renormalize_weights,
    sample_cmdb_subscore,
    sample_data_subscore,
    sample_identity_privilege_exposure,
    sample_network_subscore,
    sample_role_subscore,
)
from paper1.synthetic.fleet_generator import FleetGenerator
from paper1.utils.seeds import make_rng


def _t0_dt() -> datetime:
    return datetime.combine(date(2026, 5, 31), time(hour=0), tzinfo=UTC)


def _make_host(role: str, identity_config: str = "ad_entra_default"):
    """Build one synthetic host of the requested role."""
    gen = FleetGenerator(fleet_size=1, seed=42, identity_config=identity_config)
    # Use the generator's per-host machinery rather than full fleet to keep
    # this test deterministic and independent of distribution allocation.
    rng = make_rng(101)
    return gen.generate_host(role, 0, rng)


def test_role_subscore_in_range():
    defaults = load_host_type_defaults()
    rng = make_rng(1)
    for _ in range(50):
        s = sample_role_subscore("standard_workstation", defaults, rng)
        assert 0.0 <= s <= 1.0


def test_ipes_ad_vs_federated_for_domain_controller():
    defaults = load_host_type_defaults()
    n = 200
    ad = [
        sample_identity_privilege_exposure(
            "domain_controller", "ad_entra_default", defaults, make_rng(i)
        )
        for i in range(n)
    ]
    fed = [
        sample_identity_privilege_exposure(
            "domain_controller", "federated", defaults, make_rng(i)
        )
        for i in range(n)
    ]
    # AD config places DC at the top of the privilege hierarchy; federated
    # config lowers it because the directory authority is external.
    assert sum(ad) / n > sum(fed) / n


def test_ipes_ad_vs_federated_for_public_facing_server():
    defaults = load_host_type_defaults()
    n = 200
    ad = [
        sample_identity_privilege_exposure(
            "public_facing_server", "ad_entra_default", defaults, make_rng(i)
        )
        for i in range(n)
    ]
    fed = [
        sample_identity_privilege_exposure(
            "public_facing_server", "federated", defaults, make_rng(i)
        )
        for i in range(n)
    ]
    # Federated configuration models public-facing-server hosting an IdP,
    # so its IPES should be higher than under AD.
    assert sum(fed) / n > sum(ad) / n


def test_ipes_unknown_identity_config_raises():
    defaults = load_host_type_defaults()
    rng = make_rng(1)
    with pytest.raises(ValueError):
        sample_identity_privilege_exposure("kiosk", "unknown_config", defaults, rng)


def test_network_subscore_zone_bias():
    defaults = load_host_type_defaults()
    public = [
        sample_network_subscore("public", "public_facing_server", defaults, make_rng(i))
        for i in range(50)
    ]
    air = [
        sample_network_subscore("air_gapped", "public_facing_server", defaults, make_rng(i))
        for i in range(50)
    ]
    # Public zones should average higher than air-gapped for the same role.
    assert sum(public) / len(public) > sum(air) / len(air)


def test_data_subscore_in_range_and_cji_bonus_visible():
    defaults = load_host_type_defaults()
    n = 200
    general = [
        sample_data_subscore("general", "member_server", defaults, make_rng(i))
        for i in range(n)
    ]
    cji = [
        sample_data_subscore("cji", "member_server", defaults, make_rng(i))
        for i in range(n)
    ]
    assert all(0.0 <= s <= 1.0 for s in general + cji)
    assert sum(cji) / n > sum(general) / n


def test_cmdb_subscore_none_when_not_present():
    rng = make_rng(1)
    assert sample_cmdb_subscore(0.5, cmdb_present=False, staleness_rate=0.1, rng=rng) is None


def test_cmdb_subscore_fresh_close_to_truth():
    rng = make_rng(1)
    s = sample_cmdb_subscore(0.7, cmdb_present=True, staleness_rate=0.0, rng=rng)
    assert s is not None
    assert abs(s - 0.7) < 0.3


def test_renormalize_weights_sums_to_one():
    w = renormalize_weights(["role", "identity", "network", "data"])
    assert abs(sum(w.values()) - 1.0) < 1e-9
    assert "cmdb" not in w


def test_renormalize_no_keys_raises():
    with pytest.raises(ValueError):
        renormalize_weights([])


def test_compute_criticality_validates_schema():
    host = _make_host("domain_controller")
    defaults = load_host_type_defaults()
    cp = compute_criticality(
        host=host,
        host_defaults=defaults,
        identity_config="ad_entra_default",
        cmdb_staleness_rate=0.02,
        rng=make_rng(7),
        computed_at=_t0_dt(),
    )
    assert isinstance(cp, AssetCriticalityProfile)
    assert 0.0 <= cp.criticality_score <= 1.0


def test_domain_controller_criticality_is_high():
    host = _make_host("domain_controller")
    defaults = load_host_type_defaults()
    cp = compute_criticality(
        host=host,
        host_defaults=defaults,
        identity_config="ad_entra_default",
        cmdb_staleness_rate=0.0,
        rng=make_rng(1),
        computed_at=_t0_dt(),
    )
    assert cp.criticality_score > 0.7


def test_kiosk_criticality_is_low():
    host = _make_host("kiosk")
    defaults = load_host_type_defaults()
    cp = compute_criticality(
        host=host,
        host_defaults=defaults,
        identity_config="ad_entra_default",
        cmdb_staleness_rate=0.0,
        rng=make_rng(1),
        computed_at=_t0_dt(),
    )
    assert cp.criticality_score < 0.4


def test_missing_cmdb_renormalizes_weights():
    host = _make_host("standard_workstation")
    defaults = load_host_type_defaults()
    cp = compute_criticality(
        host=host,
        host_defaults=defaults,
        identity_config="ad_entra_default",
        cmdb_staleness_rate=0.0,
        rng=make_rng(1),
        computed_at=_t0_dt(),
        inputs_missing=["cmdb"],
    )
    assert cp.subscore_cmdb is None
    assert "cmdb" in cp.inputs_missing
    assert 0.0 <= cp.criticality_score <= 1.0


def test_computed_at_required():
    host = _make_host("standard_workstation")
    defaults = load_host_type_defaults()
    with pytest.raises(ValueError):
        compute_criticality(
            host=host,
            host_defaults=defaults,
            identity_config="ad_entra_default",
            cmdb_staleness_rate=0.0,
            rng=make_rng(1),
            computed_at=None,
        )


def test_criticality_deterministic_under_seed():
    host = _make_host("member_server")
    defaults = load_host_type_defaults()
    a = compute_criticality(
        host=host,
        host_defaults=defaults,
        identity_config="ad_entra_default",
        cmdb_staleness_rate=0.02,
        rng=make_rng(123),
        computed_at=_t0_dt(),
    )
    b = compute_criticality(
        host=host,
        host_defaults=defaults,
        identity_config="ad_entra_default",
        cmdb_staleness_rate=0.02,
        rng=make_rng(123),
        computed_at=_t0_dt(),
    )
    assert a.model_dump(mode="json") == b.model_dump(mode="json")
