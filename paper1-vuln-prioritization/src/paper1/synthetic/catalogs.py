"""Catalog loaders and shape validators for the synthetic generator."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "DEFAULT_CATALOG_DIR",
    "load_host_type_defaults",
    "load_mitigation_catalog",
    "load_os_catalog",
    "load_product_catalog",
    "load_service_catalog",
    "load_yaml_catalog",
    "validate_host_defaults",
    "validate_os_catalog",
    "validate_product_catalog",
]


def _repo_root() -> Path:
    # paper1/synthetic/catalogs.py → paper1/synthetic → paper1 → src → repo
    return Path(__file__).resolve().parents[3]


DEFAULT_CATALOG_DIR = _repo_root() / "data" / "catalog"


def load_yaml_catalog(path: str | Path) -> Any:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Catalog file not found: {p}")
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_product_catalog(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path) if path else DEFAULT_CATALOG_DIR / "products.yaml"
    return load_yaml_catalog(p)


def load_os_catalog(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path) if path else DEFAULT_CATALOG_DIR / "os_catalog.yaml"
    return load_yaml_catalog(p)


def load_host_type_defaults(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path) if path else DEFAULT_CATALOG_DIR / "host_type_defaults.yaml"
    return load_yaml_catalog(p)


def load_mitigation_catalog(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path) if path else DEFAULT_CATALOG_DIR / "mitigation_catalog.yaml"
    return load_yaml_catalog(p)


def load_service_catalog(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path) if path else DEFAULT_CATALOG_DIR / "service_catalog.yaml"
    return load_yaml_catalog(p)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _check_priors(priors: dict[str, float], where: str) -> None:
    for k, v in priors.items():
        if not isinstance(v, (int, float)):
            raise ValueError(f"{where}: prior for {k!r} must be numeric, got {type(v).__name__}")
        if not (0.0 <= float(v) <= 1.0):
            raise ValueError(f"{where}: prior for {k!r} = {v} outside [0, 1]")


def validate_product_catalog(catalog: dict[str, Any]) -> None:
    if "products" not in catalog or not isinstance(catalog["products"], list):
        raise ValueError("Product catalog missing 'products' list")
    seen: set[str] = set()
    for i, p in enumerate(catalog["products"]):
        required = {"product_key", "vendor", "product", "category", "supported_os", "version_history"}
        missing = required - set(p.keys())
        if missing:
            raise ValueError(f"Product index {i} missing required keys: {sorted(missing)}")
        pk = p["product_key"]
        if pk in seen:
            raise ValueError(f"Duplicate product_key: {pk!r}")
        seen.add(pk)
        if not isinstance(p["supported_os"], list) or not p["supported_os"]:
            raise ValueError(f"{pk}: supported_os must be a non-empty list")
        vh = p.get("version_history") or []
        if not vh:
            raise ValueError(f"{pk}: version_history must be non-empty")
        # release_date must be a date or ISO string parseable to one.
        for v in vh:
            if "version" not in v or "release_date" not in v:
                raise ValueError(f"{pk}: version_history entry missing keys: {v!r}")
        if "install_priors_by_role" in p:
            _check_priors(p["install_priors_by_role"], f"{pk}.install_priors_by_role")
        for k in ("service_running_prior", "mitigation_prior", "deployment_channel_available", "reboot_required_prior"):
            if k in p:
                _check_priors({k: p[k]}, f"{pk}")


def validate_os_catalog(catalog: dict[str, Any]) -> None:
    if "families" not in catalog or not isinstance(catalog["families"], dict):
        raise ValueError("OS catalog missing 'families' dict")
    for family, body in catalog["families"].items():
        if "versions" not in body or not body["versions"]:
            raise ValueError(f"OS family {family!r} missing non-empty 'versions'")
        for v in body["versions"]:
            if "version" not in v or "release_date" not in v:
                raise ValueError(f"OS family {family!r} version entry missing keys: {v!r}")
        if "role_priors" in body:
            _check_priors(body["role_priors"], f"os.{family}.role_priors")


def validate_host_defaults(catalog: dict[str, Any]) -> None:
    if "host_types" not in catalog or not isinstance(catalog["host_types"], dict):
        raise ValueError("Host defaults missing 'host_types' dict")
    total = 0.0
    for role, body in catalog["host_types"].items():
        required = {
            "distribution",
            "patch_lag_mean_days",
            "role_subscore_range",
            "ipes_ad_entra",
            "ipes_federated",
            "network_subscore_range",
            "data_subscore_range",
            "zone_priors",
        }
        missing = required - set(body.keys())
        if missing:
            raise ValueError(f"host_type {role!r} missing required keys: {sorted(missing)}")
        d = float(body["distribution"])
        if not (0.0 <= d <= 1.0):
            raise ValueError(f"host_type {role!r} distribution {d} outside [0, 1]")
        total += d
        for k in ("role_subscore_range", "ipes_ad_entra", "ipes_federated",
                  "network_subscore_range", "data_subscore_range"):
            rng = body[k]
            if not isinstance(rng, list) or len(rng) != 2:
                raise ValueError(f"host_type {role!r}.{k} must be a [lo, hi] pair")
            lo, hi = float(rng[0]), float(rng[1])
            if not (0.0 <= lo <= hi <= 1.0):
                raise ValueError(f"host_type {role!r}.{k} range {rng} invalid")
        _check_priors(body["zone_priors"], f"host_type {role}.zone_priors")
    if not (0.99 <= total <= 1.01):
        warnings.warn(
            f"Host-type distribution sums to {total:.4f}; will be normalized at use.",
            stacklevel=2,
        )
