"""Synthetic fleet generator (Phase 3).

Public-sector-shaped synthetic endpoints with deterministic, seed-based
generation. No employer-specific data; every parameter is published as
part of the artifact's catalog fixtures.
"""

from paper1.synthetic.catalogs import (
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
from paper1.synthetic.criticality import (
    compute_criticality,
    sample_data_subscore,
    sample_identity_privilege_exposure,
    sample_network_subscore,
    sample_role_subscore,
)
from paper1.synthetic.exposure import compute_exposure
from paper1.synthetic.fleet_generator import (
    FleetGenerator,
    generate_synthetic_fleet_bundle,
)
from paper1.synthetic.patch_state import (
    derive_patch_state,
    sample_patch_lag_days,
    sample_scan_time,
)
from paper1.synthetic.remediation_complexity import compute_complexity
from paper1.synthetic.software_inventory import (
    cpe_for_product,
    sample_inventory,
    sample_product_installed,
    sample_version,
)
from paper1.synthetic.telemetry import (
    sample_last_seen_per_source,
    sample_missing_telemetry_fields,
    telemetry_staleness_flags,
)

__all__ = [
    "FleetGenerator",
    "compute_complexity",
    "compute_criticality",
    "compute_exposure",
    "cpe_for_product",
    "derive_patch_state",
    "generate_synthetic_fleet_bundle",
    "load_host_type_defaults",
    "load_mitigation_catalog",
    "load_os_catalog",
    "load_product_catalog",
    "load_service_catalog",
    "load_yaml_catalog",
    "sample_data_subscore",
    "sample_identity_privilege_exposure",
    "sample_inventory",
    "sample_last_seen_per_source",
    "sample_missing_telemetry_fields",
    "sample_network_subscore",
    "sample_patch_lag_days",
    "sample_product_installed",
    "sample_role_subscore",
    "sample_scan_time",
    "sample_version",
    "telemetry_staleness_flags",
    "validate_host_defaults",
    "validate_os_catalog",
    "validate_product_catalog",
]
