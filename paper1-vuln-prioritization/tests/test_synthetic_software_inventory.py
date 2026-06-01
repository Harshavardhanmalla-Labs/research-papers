"""Software inventory generation tests."""

from __future__ import annotations

from datetime import date

import pytest

from paper1.audit.schema import InstalledSoftware
from paper1.synthetic.catalogs import load_product_catalog
from paper1.synthetic.software_inventory import (
    cpe_for_product,
    sample_inventory,
    sample_product_installed,
    sample_version,
)
from paper1.utils.seeds import make_rng


def _toy_product(release_dates: list[str]) -> dict:
    return {
        "product_key": "toy",
        "vendor": "Test",
        "product": "Toy",
        "category": "browser",
        "supported_os": ["linux"],
        "install_priors_by_role": {"member_server": 0.5},
        "version_history": [
            {"version": f"v{i}", "release_date": rd}
            for i, rd in enumerate(release_dates)
        ],
    }


def test_cpe_for_product_canonical_form():
    p = _toy_product(["2024-01-01"])
    cpe = cpe_for_product(p, "1.0.0")
    assert cpe == "cpe:2.3:a:test:toy:1.0.0:*:*:*:*:*:*:*"


def test_sample_product_installed_returns_false_unsupported_os():
    p = _toy_product(["2024-01-01"])
    rng = make_rng(1)
    assert not sample_product_installed(p, "member_server", "windows_server", rng)


def test_sample_product_installed_returns_false_no_prior():
    p = _toy_product(["2024-01-01"])
    p["install_priors_by_role"] = {"member_server": 0.0}
    assert not sample_product_installed(p, "member_server", "linux", make_rng(1))


def test_sample_product_installed_always_returns_true_for_prior_one():
    p = _toy_product(["2024-01-01"])
    p["install_priors_by_role"] = {"member_server": 1.0}
    assert sample_product_installed(p, "member_server", "linux", make_rng(1))


def test_sample_version_picks_latest_before_target():
    p = _toy_product(["2024-01-01", "2024-06-01", "2024-12-01"])
    v = sample_version(p, date(2024, 8, 1), patch_lag_days=0, rng=make_rng(1))
    # Target install date 2024-08-01 → latest release_date <= target is 2024-06-01.
    assert v == "v1"


def test_sample_version_respects_patch_lag():
    p = _toy_product(["2024-01-01", "2024-06-01", "2024-12-01"])
    # 90-day patch lag from 2024-12-31 → target 2024-10-02 → latest 2024-06-01.
    v = sample_version(p, date(2024, 12, 31), patch_lag_days=90, rng=make_rng(1))
    assert v == "v1"


def test_sample_version_fallback_to_earliest():
    p = _toy_product(["2026-12-01"])  # no version before any reasonable t0
    v = sample_version(p, date(2024, 1, 1), patch_lag_days=0, rng=make_rng(1))
    assert v == "v0"


def test_sample_version_empty_history_raises():
    p = _toy_product(["2024-01-01"])
    p["version_history"] = []
    with pytest.raises(ValueError):
        sample_version(p, date(2024, 6, 1), patch_lag_days=0, rng=make_rng(1))


def test_inventory_deterministic_under_seed():
    cat = load_product_catalog()
    a = sample_inventory(
        host_role="member_server",
        host_os="linux",
        t0=date(2026, 5, 31),
        patch_lag_days=14,
        product_catalog=cat,
        rng=make_rng(99),
    )
    b = sample_inventory(
        host_role="member_server",
        host_os="linux",
        t0=date(2026, 5, 31),
        patch_lag_days=14,
        product_catalog=cat,
        rng=make_rng(99),
    )
    assert [s.cpe for s in a] == [s.cpe for s in b]
    assert [s.version for s in a] == [s.version for s in b]


def test_inventory_no_duplicate_products():
    cat = load_product_catalog()
    inv = sample_inventory(
        host_role="member_server",
        host_os="linux",
        t0=date(2026, 5, 31),
        patch_lag_days=14,
        product_catalog=cat,
        rng=make_rng(1),
    )
    seen = set()
    for s in inv:
        key = (s.vendor.lower(), s.product.lower())
        assert key not in seen
        seen.add(key)


def test_inventory_versions_not_newer_than_t0():
    cat = load_product_catalog()
    t0 = date(2024, 6, 30)
    inv = sample_inventory(
        host_role="member_server",
        host_os="linux",
        t0=t0,
        patch_lag_days=0,
        product_catalog=cat,
        rng=make_rng(2),
    )
    # Every chosen version's release_date should be <= t0.
    products_by_name = {p["product"].lower(): p for p in cat["products"]}
    for s in inv:
        prod = products_by_name[s.product.lower()]
        for v in prod["version_history"]:
            if str(v["version"]) == s.version:
                rd = v["release_date"]
                rd_date = rd if isinstance(rd, date) else date.fromisoformat(str(rd))
                # Allow fallback-to-earliest case: rd may be > t0 only when
                # no version predates t0. Otherwise must be <= t0.
                earliest = min(
                    (
                        x["release_date"] if isinstance(x["release_date"], date)
                        else date.fromisoformat(str(x["release_date"]))
                    )
                    for x in prod["version_history"]
                )
                if earliest <= t0:
                    assert rd_date <= t0
                break


def test_inventory_items_validate_schema():
    cat = load_product_catalog()
    inv = sample_inventory(
        host_role="standard_workstation",
        host_os="windows_workstation",
        t0=date(2026, 5, 31),
        patch_lag_days=21,
        product_catalog=cat,
        rng=make_rng(5),
    )
    for s in inv:
        assert isinstance(s, InstalledSoftware)
