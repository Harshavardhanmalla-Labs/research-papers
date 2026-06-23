"""Catalog loader and validation tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from paper1.synthetic.catalogs import (
    DEFAULT_CATALOG_DIR,
    load_host_type_defaults,
    load_mitigation_catalog,
    load_os_catalog,
    load_product_catalog,
    load_service_catalog,
    load_yaml_catalog,
    validate_host_defaults,
    validate_os_catalog,
    validate_product_catalog,
)


def test_default_catalog_dir_exists():
    assert DEFAULT_CATALOG_DIR.exists()
    assert (DEFAULT_CATALOG_DIR / "products.yaml").exists()
    assert (DEFAULT_CATALOG_DIR / "os_catalog.yaml").exists()
    assert (DEFAULT_CATALOG_DIR / "host_type_defaults.yaml").exists()
    assert (DEFAULT_CATALOG_DIR / "service_catalog.yaml").exists()
    assert (DEFAULT_CATALOG_DIR / "mitigation_catalog.yaml").exists()


def test_load_yaml_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_yaml_catalog(tmp_path / "nope.yaml")


def test_product_catalog_has_at_least_25_entries():
    cat = load_product_catalog()
    assert len(cat["products"]) >= 25


def test_product_catalog_validates():
    cat = load_product_catalog()
    validate_product_catalog(cat)


def test_product_catalog_no_duplicate_keys():
    cat = load_product_catalog()
    keys = [p["product_key"] for p in cat["products"]]
    assert len(keys) == len(set(keys))


def test_product_version_histories_sortable():
    cat = load_product_catalog()
    for p in cat["products"]:
        dates = []
        for v in p["version_history"]:
            rd = v["release_date"]
            if isinstance(rd, date):
                dates.append(rd)
            else:
                dates.append(date.fromisoformat(str(rd)))
        # Sorting must not raise; presence proves uniform comparable type.
        sorted_dates = sorted(dates)
        assert sorted_dates == sorted(sorted_dates)


def test_product_priors_in_unit_interval():
    cat = load_product_catalog()
    for p in cat["products"]:
        priors = p.get("install_priors_by_role") or {}
        for role, v in priors.items():
            assert 0.0 <= float(v) <= 1.0, f"{p['product_key']}/{role} prior {v} out of range"


def test_os_catalog_validates():
    cat = load_os_catalog()
    validate_os_catalog(cat)


def test_os_catalog_contains_required_families():
    cat = load_os_catalog()
    families = set(cat["families"].keys())
    expected = {"windows_workstation", "windows_server", "linux", "macos", "ios", "android"}
    assert expected.issubset(families)


def test_host_defaults_validates():
    cat = load_host_type_defaults()
    validate_host_defaults(cat)


def test_host_defaults_distribution_sums_to_one():
    cat = load_host_type_defaults()
    total = sum(float(body["distribution"]) for body in cat["host_types"].values())
    assert 0.99 <= total <= 1.01


def test_host_defaults_contains_required_roles():
    cat = load_host_type_defaults()
    roles = set(cat["host_types"].keys())
    expected = {
        "standard_workstation",
        "privileged_workstation",
        "member_server",
        "domain_controller",
        "kiosk",
        "mobile_device",
        "public_facing_server",
        "restricted_zone_system",
        "buffer",
    }
    assert expected.issubset(roles)


def test_mitigation_catalog_loads():
    cat = load_mitigation_catalog()
    assert "mitigations" in cat
    for category, options in cat["mitigations"].items():
        for opt in options:
            assert 0.0 <= float(opt["prior"]) <= 1.0


def test_service_catalog_loads():
    cat = load_service_catalog()
    assert "services" in cat
    assert "openssh_server" in cat["services"]
    assert "iis" in cat["services"]


def test_validate_product_catalog_rejects_missing_products():
    with pytest.raises(ValueError):
        validate_product_catalog({})


def test_validate_product_catalog_rejects_duplicate_keys():
    bad = {
        "products": [
            {
                "product_key": "dup",
                "vendor": "v",
                "product": "p",
                "category": "browser",
                "supported_os": ["linux"],
                "version_history": [{"version": "1", "release_date": "2024-01-01"}],
            },
            {
                "product_key": "dup",
                "vendor": "v",
                "product": "p",
                "category": "browser",
                "supported_os": ["linux"],
                "version_history": [{"version": "1", "release_date": "2024-01-01"}],
            },
        ]
    }
    with pytest.raises(ValueError):
        validate_product_catalog(bad)


def test_validate_host_defaults_rejects_missing_keys():
    bad = {"host_types": {"role": {"distribution": 0.5}}}
    with pytest.raises(ValueError):
        validate_host_defaults(bad)


def test_validate_host_defaults_warns_on_non_unit_sum(tmp_path: Path):
    cat = load_host_type_defaults()
    # Add an extra role to push the sum off 1.0 and check that a warning fires.
    cat["host_types"]["extra"] = {
        "distribution": 0.5,
        "patch_lag_mean_days": 14,
        "role_subscore_range": [0.1, 0.2],
        "ipes_ad_entra": [0.1, 0.2],
        "ipes_federated": [0.1, 0.2],
        "network_subscore_range": [0.1, 0.2],
        "data_subscore_range": [0.1, 0.2],
        "zone_priors": {"internal": 1.0},
    }
    with pytest.warns(UserWarning):
        validate_host_defaults(cat)
