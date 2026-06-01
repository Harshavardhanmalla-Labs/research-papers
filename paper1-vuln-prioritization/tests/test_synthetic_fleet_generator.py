"""FleetGenerator end-to-end tests."""

from __future__ import annotations

from datetime import date

import pytest

from paper1.audit.schema import Host
from paper1.synthetic.fleet_generator import (
    FleetGenerator,
    generate_synthetic_fleet_bundle,
)


def _hosts_serializable(hosts):
    return [h.model_dump(mode="json") for h in hosts]


# -----------------------------------------------------------------------
# Determinism
# -----------------------------------------------------------------------


def test_fleet_byte_identical_under_same_seed():
    a = FleetGenerator(fleet_size=200, seed=2026, t0=date(2026, 5, 31)).generate()
    b = FleetGenerator(fleet_size=200, seed=2026, t0=date(2026, 5, 31)).generate()
    assert _hosts_serializable(a) == _hosts_serializable(b)


def test_different_seed_produces_different_fleet():
    a = FleetGenerator(fleet_size=200, seed=1, t0=date(2026, 5, 31)).generate()
    b = FleetGenerator(fleet_size=200, seed=2, t0=date(2026, 5, 31)).generate()
    # Host IDs encode the seed so they cannot collide.
    a_ids = {h.host_id for h in a}
    b_ids = {h.host_id for h in b}
    assert a_ids != b_ids


# -----------------------------------------------------------------------
# Size, uniqueness, schema validation
# -----------------------------------------------------------------------


def test_fleet_size_exact():
    for n in [10, 100, 250, 999]:
        gen = FleetGenerator(fleet_size=n, seed=1, t0=date(2026, 5, 31))
        hosts = gen.generate()
        assert len(hosts) == n


def test_host_ids_unique():
    gen = FleetGenerator(fleet_size=500, seed=1, t0=date(2026, 5, 31))
    hosts = gen.generate()
    ids = [h.host_id for h in hosts]
    assert len(ids) == len(set(ids))


def test_every_host_validates_schema():
    gen = FleetGenerator(fleet_size=100, seed=1, t0=date(2026, 5, 31))
    hosts = gen.generate()
    for h in hosts:
        assert isinstance(h, Host)
        assert h.group_id.startswith("G-")
        assert h.network_zone in {"public", "dmz", "internal", "restricted", "air_gapped"}


def test_hosts_sorted_deterministically():
    gen = FleetGenerator(fleet_size=100, seed=1, t0=date(2026, 5, 31))
    hosts = gen.generate()
    ids = [h.host_id for h in hosts]
    assert ids == sorted(ids)


# -----------------------------------------------------------------------
# Allocation + distribution tolerance
# -----------------------------------------------------------------------


def test_allocate_host_types_sums_to_fleet_size():
    gen = FleetGenerator(fleet_size=1000, seed=1, t0=date(2026, 5, 31))
    alloc = gen.allocate_host_types()
    assert sum(alloc.values()) == 1000


def test_distribution_within_tolerance():
    n = 10_000
    gen = FleetGenerator(fleet_size=n, seed=1, t0=date(2026, 5, 31))
    hosts = gen.generate()
    realized = gen.verify_distribution(hosts)
    targets = {
        role: float(body["distribution"])
        for role, body in gen.host_defaults["host_types"].items()
    }
    # With 10k hosts and the smallest target proportion 0.005, the
    # absolute deviation should be well under 0.01.
    for role, target in targets.items():
        if target == 0.0:
            continue
        assert abs(realized.get(role, 0.0) - target) < 0.01, (role, realized.get(role), target)


# -----------------------------------------------------------------------
# OS assignment rules
# -----------------------------------------------------------------------


def test_domain_controllers_are_windows_server():
    gen = FleetGenerator(fleet_size=2000, seed=1, t0=date(2026, 5, 31))
    hosts = gen.generate()
    dcs = [h for h in hosts if h.role == "domain_controller"]
    assert dcs, "expected at least one domain controller in 2000-host fleet"
    for h in dcs:
        assert h.os_family == "windows_server"


def test_mobile_devices_are_mobile_oses():
    gen = FleetGenerator(fleet_size=2000, seed=1, t0=date(2026, 5, 31))
    hosts = gen.generate()
    mobiles = [h for h in hosts if h.role == "mobile_device"]
    assert mobiles, "expected mobile devices in 2000-host fleet"
    for h in mobiles:
        assert h.os_family in {"ios", "android"}


def test_public_facing_servers_are_server_oses():
    gen = FleetGenerator(fleet_size=2000, seed=1, t0=date(2026, 5, 31))
    hosts = gen.generate()
    pfs = [h for h in hosts if h.role == "public_facing_server"]
    assert pfs, "expected public-facing servers in 2000-host fleet"
    for h in pfs:
        assert h.os_family in {"linux", "windows_server"}


# -----------------------------------------------------------------------
# Group assignment
# -----------------------------------------------------------------------


def test_group_assignment_uses_role_prefix():
    gen = FleetGenerator(fleet_size=200, seed=1, t0=date(2026, 5, 31))
    hosts = gen.generate()
    for h in hosts:
        assert h.group_id.startswith(f"G-{h.role}-")


# -----------------------------------------------------------------------
# Constructor validation
# -----------------------------------------------------------------------


def test_constructor_rejects_bad_fleet_size():
    with pytest.raises(ValueError):
        FleetGenerator(fleet_size=0, seed=1, t0=date(2026, 5, 31))


def test_constructor_rejects_negative_seed():
    with pytest.raises(ValueError):
        FleetGenerator(fleet_size=1, seed=-1, t0=date(2026, 5, 31))


def test_constructor_rejects_unknown_identity_config_at_generate():
    gen = FleetGenerator(
        fleet_size=100, seed=1, t0=date(2026, 5, 31), identity_config="foo"
    )
    # Identity config is consumed when sampling tier; calling generate exercises it.
    with pytest.raises(ValueError):
        gen.generate()


# -----------------------------------------------------------------------
# Bundle
# -----------------------------------------------------------------------


def test_generate_bundle_for_100_hosts():
    bundle = generate_synthetic_fleet_bundle(
        fleet_size=100, seed=1, t0=date(2026, 5, 31)
    )
    assert len(bundle["hosts"]) == 100
    assert len(bundle["criticality"]) == 100
    host_ids = {h.host_id for h in bundle["hosts"]}
    crit_ids = {c.host_id for c in bundle["criticality"]}
    assert host_ids == crit_ids


def test_bundle_deterministic_serialization():
    a = generate_synthetic_fleet_bundle(
        fleet_size=50, seed=7, t0=date(2026, 5, 31)
    )
    b = generate_synthetic_fleet_bundle(
        fleet_size=50, seed=7, t0=date(2026, 5, 31)
    )
    assert [h.model_dump(mode="json") for h in a["hosts"]] == [
        h.model_dump(mode="json") for h in b["hosts"]
    ]
    assert [c.model_dump(mode="json") for c in a["criticality"]] == [
        c.model_dump(mode="json") for c in b["criticality"]
    ]


def test_bundle_federated_identity_changes_dc_ipes():
    """Sanity: DC IPES distribution differs between AD and federated configs."""
    ad = generate_synthetic_fleet_bundle(
        fleet_size=500, seed=11, t0=date(2026, 5, 31), identity_config="ad_entra_default"
    )
    fed = generate_synthetic_fleet_bundle(
        fleet_size=500, seed=11, t0=date(2026, 5, 31), identity_config="federated"
    )
    ad_dc_ipes = [
        c.subscore_identity for c in ad["criticality"]
        if any(h.host_id == c.host_id and h.role == "domain_controller" for h in ad["hosts"])
    ]
    fed_dc_ipes = [
        c.subscore_identity for c in fed["criticality"]
        if any(h.host_id == c.host_id and h.role == "domain_controller" for h in fed["hosts"])
    ]
    # At fleet_size=500 with 0.5% DC proportion we expect at least one DC.
    if ad_dc_ipes and fed_dc_ipes:
        assert sum(ad_dc_ipes) / len(ad_dc_ipes) > sum(fed_dc_ipes) / len(fed_dc_ipes)
