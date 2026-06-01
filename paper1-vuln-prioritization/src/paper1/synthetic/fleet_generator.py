"""FleetGenerator: produce a deterministic synthetic endpoint fleet."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import Any

import numpy as np

from paper1.audit.schema import AssetCriticalityProfile, Host
from paper1.synthetic.catalogs import (
    load_host_type_defaults,
    load_os_catalog,
    load_product_catalog,
    validate_host_defaults,
    validate_os_catalog,
    validate_product_catalog,
)
from paper1.synthetic.criticality import compute_criticality
from paper1.synthetic.patch_state import derive_patch_state, sample_patch_lag_days
from paper1.synthetic.software_inventory import sample_inventory
from paper1.synthetic.telemetry import (
    TELEMETRY_SOURCES,
    sample_last_seen_per_source,
    sample_missing_telemetry_fields,
    telemetry_staleness_flags,
)
from paper1.utils.seeds import derive_subseed, make_rng
from paper1.utils.time import parse_date

__all__ = ["FleetGenerator", "generate_synthetic_fleet_bundle"]


class FleetGenerator:
    """Generate a deterministic synthetic fleet from a (config, seed) pair.

    The generator is intentionally narrow: it does not produce
    vulnerabilities, pairs, scores, or scheduling decisions. Downstream
    phases consume its output via the existing Pydantic schemas.
    """

    def __init__(
        self,
        fleet_size: int,
        seed: int,
        host_defaults: dict[str, Any] | None = None,
        os_catalog: dict[str, Any] | None = None,
        product_catalog: dict[str, Any] | None = None,
        identity_config: str = "ad_entra_default",
        t0: date | datetime | str = "2026-05-31",
        cmdb_staleness_rate: float = 0.02,
        telemetry_missingness_rate: float = 0.05,
        cmdb_presence_prior: float = 0.85,
    ) -> None:
        if fleet_size <= 0:
            raise ValueError(f"fleet_size must be > 0; got {fleet_size}")
        if not isinstance(seed, int) or seed < 0:
            raise ValueError(f"seed must be a non-negative int; got {seed!r}")
        if not (0.0 <= cmdb_staleness_rate <= 1.0):
            raise ValueError("cmdb_staleness_rate must be in [0, 1]")
        if not (0.0 <= telemetry_missingness_rate <= 1.0):
            raise ValueError("telemetry_missingness_rate must be in [0, 1]")
        if not (0.0 <= cmdb_presence_prior <= 1.0):
            raise ValueError("cmdb_presence_prior must be in [0, 1]")

        self.fleet_size = int(fleet_size)
        self.seed = int(seed)
        self.identity_config = identity_config
        self.cmdb_staleness_rate = float(cmdb_staleness_rate)
        self.telemetry_missingness_rate = float(telemetry_missingness_rate)
        self.cmdb_presence_prior = float(cmdb_presence_prior)

        self.host_defaults = host_defaults or load_host_type_defaults()
        self.os_catalog = os_catalog or load_os_catalog()
        self.product_catalog = product_catalog or load_product_catalog()
        validate_host_defaults(self.host_defaults)
        validate_os_catalog(self.os_catalog)
        validate_product_catalog(self.product_catalog)

        if isinstance(t0, datetime):
            self.t0: date = t0.date()
        elif isinstance(t0, date):
            self.t0 = t0
        elif isinstance(t0, str):
            self.t0 = parse_date(t0)
        else:
            raise TypeError(f"t0 must be date|datetime|str; got {type(t0).__name__}")

        self._t0_dt = datetime.combine(self.t0, time(hour=0), tzinfo=UTC)

    # ----- public API ------------------------------------------------------

    def allocate_host_types(self) -> dict[str, int]:
        """Allocate integer host counts per role summing exactly to fleet_size.

        Distribution proportions from the host_defaults catalog are
        normalized. The allocation rounds and assigns any remainder to
        the largest category for determinism.
        """
        types = self.host_defaults["host_types"]
        proportions = {role: float(body["distribution"]) for role, body in types.items()}
        total = sum(proportions.values())
        if total <= 0.0:
            raise ValueError("host_types distribution sums to zero")
        normalized = {k: v / total for k, v in proportions.items()}
        raw = {k: self.fleet_size * v for k, v in normalized.items()}
        floors = {k: int(np.floor(v)) for k, v in raw.items()}
        remainder = self.fleet_size - sum(floors.values())
        # Assign the remainder to roles with the largest fractional parts
        # (deterministic by role name for ties).
        fractional = sorted(
            ((k, raw[k] - floors[k]) for k in raw),
            key=lambda kv: (-kv[1], kv[0]),
        )
        for i in range(remainder):
            role = fractional[i % len(fractional)][0]
            floors[role] += 1
        return floors

    def assign_group(self, host_role: str, index: int) -> str:
        role_cfg = self.host_defaults["host_types"][host_role]
        group_size = int(role_cfg.get("group_size", 100))
        group_index = index // max(1, group_size)
        return f"G-{host_role}-{group_index:04d}"

    def generate_host(
        self,
        host_type: str,
        role_index: int,
        rng: np.random.Generator,
    ) -> Host:
        os_family, os_version = self._sample_os(host_type, rng)
        zone = self._sample_zone(host_type, rng)
        identity_tier = self._sample_identity_tier(host_type, rng)
        data_sensitivity = self._sample_data_sensitivity(host_type, rng)

        patch_lag = sample_patch_lag_days(host_type, self.host_defaults, rng)
        inventory = sample_inventory(
            host_role=host_type,
            host_os=os_family,
            t0=self.t0,
            patch_lag_days=patch_lag,
            product_catalog=self.product_catalog,
            rng=rng,
        )
        patch_state = derive_patch_state([], self.t0, scan_source="synthetic", rng=rng)

        last_seen = sample_last_seen_per_source(self.t0, host_type, rng)
        missing_fields = sample_missing_telemetry_fields(
            TELEMETRY_SOURCES, self.telemetry_missingness_rate, rng
        )
        staleness = telemetry_staleness_flags(last_seen, self.t0)

        cmdb_tags: dict[str, str] | None = None
        if rng.random() < self.cmdb_presence_prior:
            cmdb_tags = {
                "owner": f"team-{host_type}",
                "criticality_bucket": self._bucket_for_role(host_type),
            }

        host_id = f"H-{host_type}-{role_index:06d}-s{self.seed}"
        return Host(
            host_id=host_id,
            os_family=os_family,
            os_version=os_version,
            role=host_type,
            network_zone=zone,
            identity_tier=identity_tier,
            data_sensitivity_proxy=data_sensitivity,
            installed_software=inventory,
            patch_state=patch_state,
            last_seen_per_source=last_seen,
            staleness_flags=sorted(set(staleness + [f"missing:{m}" for m in missing_fields])),
            cmdb_tags=cmdb_tags,
            group_id=self.assign_group(host_type, role_index),
        )

    def generate(self) -> list[Host]:
        """Generate the full fleet, sorted deterministically by host_id."""
        allocation = self.allocate_host_types()
        if sum(allocation.values()) != self.fleet_size:
            raise AssertionError("host_type allocation did not match fleet_size")
        hosts: list[Host] = []
        for host_type in sorted(allocation):
            count = allocation[host_type]
            for i in range(count):
                sub = derive_subseed(self.seed, f"host|{host_type}|{i}")
                rng = make_rng(sub)
                hosts.append(self.generate_host(host_type, i, rng))
        hosts.sort(key=lambda h: h.host_id)
        # Sanity: every host validates by virtue of Pydantic construction.
        return hosts

    def verify_distribution(self, hosts: list[Host]) -> dict[str, float]:
        """Return realized role fractions; useful for tolerance tests."""
        if not hosts:
            return {}
        counts: dict[str, int] = {}
        for h in hosts:
            counts[h.role] = counts.get(h.role, 0) + 1
        total = sum(counts.values())
        return {k: counts[k] / total for k in counts}

    # ----- helpers ---------------------------------------------------------

    def _sample_os(self, host_type: str, rng: np.random.Generator) -> tuple[str, str]:
        families = self.os_catalog["families"]
        # Collect (family, prior) pairs that name this role.
        candidates: list[tuple[str, float]] = []
        for family, body in families.items():
            priors = body.get("role_priors") or {}
            p = float(priors.get(host_type, 0.0))
            if p > 0:
                candidates.append((family, p))
        if not candidates:
            raise ValueError(f"OS catalog has no role_priors for role {host_type!r}")
        total = sum(p for _, p in candidates)
        # Hard rule overrides for some roles to keep evaluation realistic.
        if host_type == "domain_controller":
            family = "windows_server"
        elif host_type == "mobile_device":
            r = rng.random() * total
            cum = 0.0
            family = "ios"
            for fam, p in candidates:
                cum += p
                if r <= cum:
                    family = fam
                    break
            if family not in {"ios", "android"}:
                family = "android"
        elif host_type == "public_facing_server":
            r = rng.random() * total
            cum = 0.0
            family = "linux"
            for fam, p in candidates:
                cum += p
                if r <= cum:
                    family = fam
                    break
            if family not in {"linux", "windows_server"}:
                family = "linux"
        else:
            r = rng.random() * total
            cum = 0.0
            family = candidates[0][0]
            for fam, p in candidates:
                cum += p
                if r <= cum:
                    family = fam
                    break

        versions = families[family]["versions"]
        # Choose version uniformly among available versions.
        idx = int(rng.integers(0, len(versions)))
        return family, str(versions[idx]["version"])

    def _sample_zone(self, host_type: str, rng: np.random.Generator) -> str:
        priors = self.host_defaults["host_types"][host_type]["zone_priors"]
        return _sample_from_prior_dict(priors, rng)

    def _sample_identity_tier(self, host_type: str, rng: np.random.Generator) -> str:
        role_cfg = self.host_defaults["host_types"][host_type]
        if self.identity_config in ("ad_entra_default", "ad_entra", "ad"):
            priors = role_cfg.get("identity_tier_priors_ad") or {}
        elif self.identity_config in ("federated", "federated_default"):
            priors = role_cfg.get("identity_tier_priors_federated") or {}
        else:
            raise ValueError(f"Unknown identity_config: {self.identity_config!r}")
        if not priors:
            return "non_ad"
        return _sample_from_prior_dict(priors, rng)

    def _sample_data_sensitivity(
        self, host_type: str, rng: np.random.Generator
    ) -> str | None:
        priors = self.host_defaults["host_types"][host_type].get("data_sensitivity_priors") or {}
        if not priors:
            return None
        return _sample_from_prior_dict(priors, rng)

    @staticmethod
    def _bucket_for_role(host_type: str) -> str:
        high = {"domain_controller", "public_facing_server", "restricted_zone_system",
                "privileged_workstation"}
        low = {"kiosk", "mobile_device"}
        if host_type in high:
            return "high"
        if host_type in low:
            return "low"
        return "medium"


def _sample_from_prior_dict(priors: dict[str, float], rng: np.random.Generator) -> str:
    """Categorical sample over a non-empty {label: prior} dict."""
    items = sorted(priors.items())
    total = sum(float(v) for _, v in items)
    if total <= 0:
        raise ValueError(f"priors sum to zero: {priors!r}")
    r = float(rng.random()) * total
    cum = 0.0
    for label, p in items:
        cum += float(p)
        if r <= cum:
            return label
    return items[-1][0]


def generate_synthetic_fleet_bundle(
    fleet_size: int,
    seed: int,
    *,
    identity_config: str = "ad_entra_default",
    t0: date | datetime | str = "2026-05-31",
    host_defaults: dict[str, Any] | None = None,
    os_catalog: dict[str, Any] | None = None,
    product_catalog: dict[str, Any] | None = None,
    cmdb_staleness_rate: float = 0.02,
    telemetry_missingness_rate: float = 0.05,
) -> dict[str, Any]:
    """Generate a (hosts, criticality) bundle aligned by host_id.

    Vulnerability-host pairs, scores, and scheduling decisions are NOT
    produced — those belong to later phases.
    """
    gen = FleetGenerator(
        fleet_size=fleet_size,
        seed=seed,
        host_defaults=host_defaults,
        os_catalog=os_catalog,
        product_catalog=product_catalog,
        identity_config=identity_config,
        t0=t0,
        cmdb_staleness_rate=cmdb_staleness_rate,
        telemetry_missingness_rate=telemetry_missingness_rate,
    )
    hosts = gen.generate()
    computed_at = gen._t0_dt
    criticality: list[AssetCriticalityProfile] = []
    for h in hosts:
        sub = derive_subseed(seed, f"criticality|{h.host_id}")
        rng = make_rng(sub)
        cp = compute_criticality(
            host=h,
            host_defaults=gen.host_defaults,
            identity_config=identity_config,
            cmdb_staleness_rate=cmdb_staleness_rate,
            rng=rng,
            computed_at=computed_at,
        )
        criticality.append(cp)
    return {"hosts": hosts, "criticality": criticality}
