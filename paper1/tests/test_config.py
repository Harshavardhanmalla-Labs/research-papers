"""Config loading and shape validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from paper1.utils.config import (
    REQUIRED_KEYS,
    config_sha256,
    load_yaml,
    validate_config_file,
)


def test_all_required_configs_present(configs_dir: Path):
    """Every config file named in REQUIRED_KEYS must exist on disk."""
    missing = [name for name in REQUIRED_KEYS if not (configs_dir / name).exists()]
    assert missing == [], f"Missing config files: {missing}"


def test_all_configs_load(configs_dir: Path):
    for name in REQUIRED_KEYS:
        payload = load_yaml(configs_dir / name)
        assert isinstance(payload, dict), f"{name} did not load as a mapping"


@pytest.mark.parametrize("name", sorted(REQUIRED_KEYS))
def test_required_keys_present(configs_dir: Path, name: str):
    payload = validate_config_file(configs_dir / name)
    missing = REQUIRED_KEYS[name] - set(payload.keys())
    assert missing == set(), f"{name} missing required keys: {sorted(missing)}"


def test_primary_yaml_strategy_list_has_expected_strategies(configs_dir: Path):
    payload = validate_config_file(configs_dir / "primary.yaml")
    strategies = set(payload["strategies"])
    expected = {
        "random",
        "cvss_only",
        "epss_only",
        "kev_first",
        "cvss_x_epss",
        "cvss_plus_epss_plus_kev",
        "cve_max",
        "cve_mean",
        "cve_sum",
        "proposed_full",
        "proposed_no_criticality",
        "proposed_no_exposure",
        "oracle",
        "gbt_comparator",
    }
    assert strategies == expected


def test_gbt_yaml_feature_set_matches_paper(configs_dir: Path):
    payload = validate_config_file(configs_dir / "gbt.yaml")
    assert set(payload["feature_set"]) == {"E", "K", "S", "C", "X", "U", "R"}


def test_config_sha_stable(configs_dir: Path, tmp_path: Path):
    src = configs_dir / "primary.yaml"
    a = config_sha256(src)
    b = config_sha256(src)
    assert a == b
    # Copy preserves bytes -> same SHA.
    dst = tmp_path / "primary.yaml"
    dst.write_bytes(src.read_bytes())
    assert config_sha256(dst) == a


def test_validate_missing_key_raises(tmp_path: Path):
    bad = tmp_path / "primary.yaml"
    bad.write_text("config_name: x\n", encoding="utf-8")
    with pytest.raises(ValueError):
        validate_config_file(bad)


def test_load_yaml_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_yaml(tmp_path / "nope.yaml")


def test_labels_yaml_has_both_labels(configs_dir: Path):
    payload = validate_config_file(configs_dir / "labels.yaml")
    assert {"A", "B"} <= set(payload["labels"].keys())


def test_strategies_yaml_count_matches_primary(configs_dir: Path):
    strategies_yaml = validate_config_file(configs_dir / "strategies.yaml")
    primary = validate_config_file(configs_dir / "primary.yaml")
    # Every strategy declared in primary must appear in strategies.yaml.
    declared = set(strategies_yaml["strategies"].keys())
    referenced = set(primary["strategies"])
    missing = referenced - declared
    assert missing == set(), f"strategies.yaml missing: {sorted(missing)}"
