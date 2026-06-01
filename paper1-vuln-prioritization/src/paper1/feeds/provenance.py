"""Snapshot manifest and per-record provenance.

The manifest is an append-style index file at
``data/snapshots/MANIFEST.json``. Every snapshot written by a fetch
script registers (or updates in place) an entry naming the source, the
as-of date, the file path, the SHA-256 of the file, and the record
count. Verification iterates every entry and reconfirms the file
SHA-256 matches the manifest.

Per-record provenance fields (source_name, source_url /
source_identifier, fetched_at, published_at or as_of_date) are attached
to each row by the feed clients themselves; ``attach_provenance``
encodes that contract.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from paper1.utils.io import atomic_write_json, compute_file_sha256, read_json
from paper1.utils.time import ensure_utc, parse_date, utc_now

__all__ = [
    "REQUIRED_PROVENANCE_FIELDS",
    "attach_provenance",
    "load_manifest",
    "snapshot_id",
    "update_manifest_entry",
    "verify_manifest",
    "verify_snapshot_file",
    "write_manifest",
]


# Per-record provenance fields that every feed must populate.
REQUIRED_PROVENANCE_FIELDS = (
    "source_name",
    "fetched_at",
)


def snapshot_id(source_name: str, snapshot_date: date) -> str:
    """Canonical key for manifest entry deduplication."""
    if not isinstance(snapshot_date, date) or isinstance(snapshot_date, datetime):
        raise TypeError("snapshot_date must be a date (not datetime)")
    return f"{source_name}|{snapshot_date.isoformat()}"


def _empty_manifest() -> dict[str, Any]:
    return {
        "generated_at": utc_now().isoformat().replace("+00:00", "Z"),
        "snapshots": [],
    }


def load_manifest(path: str | Path) -> dict[str, Any]:
    """Load a manifest, returning an empty manifest if the file is absent."""
    p = Path(path)
    if not p.exists():
        return _empty_manifest()
    payload = read_json(p)
    if not isinstance(payload, dict):
        raise ValueError(f"Manifest {p} must be a JSON object")
    if "snapshots" not in payload or not isinstance(payload["snapshots"], list):
        raise ValueError(f"Manifest {p} missing 'snapshots' list")
    return payload


def write_manifest(path: str | Path, manifest: dict[str, Any]) -> None:
    """Atomically write the manifest; refreshes generated_at."""
    payload = dict(manifest)
    payload["generated_at"] = utc_now().isoformat().replace("+00:00", "Z")
    # Sort snapshots by (source, date) for deterministic byte output.
    snapshots = list(payload.get("snapshots", []))
    snapshots.sort(key=lambda e: (e.get("source_name", ""), e.get("snapshot_date", "")))
    payload["snapshots"] = snapshots
    atomic_write_json(path, payload)


def update_manifest_entry(
    manifest_path: str | Path,
    *,
    source_name: str,
    snapshot_date: date,
    snapshot_file: str | Path,
    record_count: int,
    license_note: str = "",
    schema_version: str = "1",
) -> dict[str, Any]:
    """Insert or replace one snapshot entry; recomputes file SHA-256.

    Returns the entry dict written.
    """
    manifest = load_manifest(manifest_path)
    file_path = Path(snapshot_file)
    if not file_path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {file_path}")
    sha = compute_file_sha256(file_path)
    entry = {
        "source_name": source_name,
        "snapshot_date": snapshot_date.isoformat(),
        "path": str(file_path),
        "sha256": sha,
        "record_count": int(record_count),
        "license_note": license_note,
        "created_by": "paper1",
        "schema_version": schema_version,
    }
    sid = snapshot_id(source_name, snapshot_date)
    # Remove any existing entry with the same id; then append fresh.
    manifest["snapshots"] = [
        e
        for e in manifest["snapshots"]
        if snapshot_id(e["source_name"], parse_date(e["snapshot_date"])) != sid
    ]
    manifest["snapshots"].append(entry)
    write_manifest(manifest_path, manifest)
    return entry


def verify_snapshot_file(path: str | Path, expected_sha: str) -> bool:
    """Recompute the file SHA-256 and compare to expected."""
    actual = compute_file_sha256(path)
    return actual.lower() == expected_sha.lower()


def verify_manifest(manifest_path: str | Path) -> tuple[bool, list[str]]:
    """Verify every entry's file exists and SHA-256 matches.

    Returns ``(ok, issues)``.
    """
    issues: list[str] = []
    p = Path(manifest_path)
    if not p.exists():
        return False, [f"Manifest not found: {p}"]
    manifest = load_manifest(p)
    for entry in manifest["snapshots"]:
        file_path = Path(entry["path"])
        if not file_path.exists():
            issues.append(f"{entry['source_name']}@{entry['snapshot_date']}: file missing ({file_path})")
            continue
        if not verify_snapshot_file(file_path, entry["sha256"]):
            issues.append(
                f"{entry['source_name']}@{entry['snapshot_date']}: SHA-256 mismatch "
                f"(expected {entry['sha256']})"
            )
    return (len(issues) == 0), issues


def attach_provenance(
    record: dict[str, Any],
    *,
    source_name: str,
    fetched_at: datetime,
    source_url: str | None = None,
    source_identifier: str | None = None,
    snapshot_sha256: str | None = None,
    source_version: str | None = None,
) -> dict[str, Any]:
    """Return a new dict with provenance fields layered onto a record."""
    ensure_utc(fetched_at)
    out = dict(record)
    out["source_name"] = source_name
    out["fetched_at"] = fetched_at.isoformat().replace("+00:00", "Z")
    if source_url is not None:
        out["source_url"] = source_url
    if source_identifier is not None:
        out["source_identifier"] = source_identifier
    if snapshot_sha256 is not None:
        out["snapshot_sha256"] = snapshot_sha256
    if source_version is not None:
        out["source_version"] = source_version
    return out
