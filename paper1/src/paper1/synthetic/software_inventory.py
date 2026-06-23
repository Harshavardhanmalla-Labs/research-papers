"""Software inventory generation per host."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import numpy as np

from paper1.audit.schema import InstalledSoftware

__all__ = [
    "cpe_for_product",
    "sample_inventory",
    "sample_product_installed",
    "sample_version",
]


def cpe_for_product(product: dict[str, Any], version: str) -> str:
    """Produce a canonical-shape CPE 2.3 URI for (product, version)."""
    vendor = str(product["vendor"]).lower()
    name = str(product["product"]).lower()
    v = str(version).replace(":", "_")  # CPE field separator is ':'
    return f"cpe:2.3:a:{vendor}:{name}:{v}:*:*:*:*:*:*:*"


def sample_product_installed(
    product: dict[str, Any],
    host_role: str,
    host_os: str,
    rng: np.random.Generator,
) -> bool:
    """Decide whether this product is installed on the given host."""
    supported = product.get("supported_os") or []
    if host_os not in supported:
        return False
    priors = product.get("install_priors_by_role") or {}
    p = float(priors.get(host_role, 0.0))
    if p <= 0.0:
        return False
    if p >= 1.0:
        return True
    return bool(rng.random() < p)


def sample_version(
    product: dict[str, Any],
    t0: date,
    patch_lag_days: int,
    rng: np.random.Generator,
) -> str:
    """Pick the highest version whose release_date <= t0 - patch_lag.

    Falls back to the earliest available version when no version
    predates the target install date.
    """
    vh: list[dict[str, Any]] = list(product.get("version_history") or [])
    if not vh:
        raise ValueError(f"Product {product.get('product_key')!r} has empty version_history")

    def _as_date(v: Any) -> date:
        if isinstance(v, date):
            return v
        return date.fromisoformat(str(v))

    sorted_vh = sorted(vh, key=lambda v: _as_date(v["release_date"]))
    target = t0 - timedelta(days=max(0, int(patch_lag_days)))

    candidates = [v for v in sorted_vh if _as_date(v["release_date"]) <= target]
    if candidates:
        return str(candidates[-1]["version"])
    # Earliest version when nothing predates the target — unavoidable for
    # very fresh products on freshly-installed hosts.
    return str(sorted_vh[0]["version"])


def sample_inventory(
    host_role: str,
    host_os: str,
    t0: date,
    patch_lag_days: int,
    product_catalog: dict[str, Any],
    rng: np.random.Generator,
) -> list[InstalledSoftware]:
    """Sample the per-host installed-software list.

    The list is deduplicated by product_key and ordered by product_key
    for hash stability.
    """
    products = list(product_catalog.get("products") or [])
    selected: dict[str, InstalledSoftware] = {}
    for product in sorted(products, key=lambda p: p["product_key"]):
        pk = product["product_key"]
        if pk in selected:
            continue
        if not sample_product_installed(product, host_role, host_os, rng):
            continue
        version = sample_version(product, t0, patch_lag_days, rng)
        cpe = cpe_for_product(product, version)
        selected[pk] = InstalledSoftware(
            cpe=cpe,
            product=str(product["product"]),
            vendor=str(product["vendor"]),
            version=version,
            install_date=None,
        )
    return [selected[k] for k in sorted(selected.keys())]
