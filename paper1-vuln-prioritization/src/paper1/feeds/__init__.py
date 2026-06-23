"""Feed clients (Phase 2).

NVD, FIRST EPSS, CISA KEV, and ExploitDB/PoC clients sharing a common
base class. Every record carries provenance fields (source, fetched_at,
published/as_of date, snapshot_sha256). Every as-of query refuses to
return records published or added after the requested cutoff.

No live network calls happen during unit tests; tests use local
fixtures and monkeypatching.
"""

from paper1.feeds.base import BaseFeedClient, FutureDataError
from paper1.feeds.cve_client import (
    cpe_to_product_key,
    extract_affected_ranges,
    normalize_cpe,
    parse_cpe23,
    version_in_range,
)
from paper1.feeds.epss_client import (
    EPSS_HISTORY_BEGIN,
    EPSSClient,
    epss_snapshot_url,
    infer_epss_model_version,
    normalize_epss_csv,
)
from paper1.feeds.kev_client import KEVClient, normalize_kev_catalog
from paper1.feeds.nvd_client import (
    NVDClient,
    extract_cpe_matches,
    extract_cvss,
    normalize_nvd_record,
)
from paper1.feeds.poc_client import (
    POC_ENV_FLAG,
    POCClient,
    PoCLicenseGateError,
    extract_cves_from_exploitdb_row,
    normalize_exploitdb_csv,
)
from paper1.feeds.provenance import (
    REQUIRED_PROVENANCE_FIELDS,
    attach_provenance,
    load_manifest,
    snapshot_id,
    update_manifest_entry,
    verify_manifest,
    verify_snapshot_file,
    write_manifest,
)
from paper1.feeds.snapshots import (
    load_snapshot,
    snapshot_path,
    write_snapshot,
)

__all__ = [
    "EPSS_HISTORY_BEGIN",
    "POC_ENV_FLAG",
    "REQUIRED_PROVENANCE_FIELDS",
    "BaseFeedClient",
    "EPSSClient",
    "FutureDataError",
    "KEVClient",
    "NVDClient",
    "POCClient",
    "PoCLicenseGateError",
    "attach_provenance",
    "cpe_to_product_key",
    "epss_snapshot_url",
    "extract_affected_ranges",
    "extract_cpe_matches",
    "extract_cves_from_exploitdb_row",
    "extract_cvss",
    "infer_epss_model_version",
    "load_manifest",
    "load_snapshot",
    "normalize_cpe",
    "normalize_epss_csv",
    "normalize_exploitdb_csv",
    "normalize_kev_catalog",
    "normalize_nvd_record",
    "parse_cpe23",
    "snapshot_id",
    "snapshot_path",
    "update_manifest_entry",
    "verify_manifest",
    "verify_snapshot_file",
    "version_in_range",
    "write_manifest",
    "write_snapshot",
]
