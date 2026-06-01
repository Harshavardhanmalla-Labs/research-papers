"""Append-only hash-chained audit log.

Every decision produces an `AuditDecisionRecord`. Each record's
`record_hash` is the SHA-256 of its canonical JSON serialization with
`record_hash` itself excluded. Each record's `prior_record_hash`
references the previous record's `record_hash`. The genesis prior hash
is 64 zeros.

The chain is tamper-evident: any modification to a stored record's
content changes its computed hash, which breaks both that record's
self-hash check and the next record's chain link.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from paper1.audit.schema import AuditDecisionRecord
from paper1.utils.io import write_jsonl

__all__ = [
    "GENESIS_PRIOR_HASH",
    "AuditLogger",
    "compute_record_hash",
    "compute_record_payload_hash",
    "verify_chain",
]

GENESIS_PRIOR_HASH = "0" * 64

# Fields excluded from the canonical hash payload. `record_hash` is
# always excluded because we are computing it.
_EXCLUDED_FROM_HASH = {"record_hash"}


def _canonical_payload(record: AuditDecisionRecord) -> str:
    """Canonical JSON form used as the hashing input."""
    raw = record.model_dump(mode="json", exclude=_EXCLUDED_FROM_HASH)
    return json.dumps(raw, sort_keys=True, separators=(",", ":"), default=str)


def compute_record_payload_hash(record: AuditDecisionRecord) -> str:
    """SHA-256 of the record's canonical payload (alias of compute_record_hash)."""
    return hashlib.sha256(_canonical_payload(record).encode("utf-8")).hexdigest()


def compute_record_hash(record: AuditDecisionRecord) -> str:
    """SHA-256 of the canonical payload, excluding record_hash itself.

    The `prior_record_hash` IS included in the hashed payload, which is
    what makes the chain tamper-evident.
    """
    return compute_record_payload_hash(record)


def verify_chain(
    path: str | Path,
) -> tuple[bool, list[str]]:
    """Verify a hash-chained JSONL audit log.

    Returns ``(ok, issues)``. ``ok`` is True iff there are no issues.
    """
    issues: list[str] = []
    prior_hash = GENESIS_PRIOR_HASH
    p = Path(path)
    if not p.exists():
        return False, [f"Audit log not found: {p}"]

    with open(p, encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload: dict[str, Any] = json.loads(line)
            except json.JSONDecodeError as exc:
                issues.append(f"Line {line_no}: invalid JSON ({exc})")
                return False, issues

            try:
                record = AuditDecisionRecord(**payload)
            except Exception as exc:  # pragma: no cover - exercised in tests
                issues.append(f"Line {line_no}: schema validation failed ({exc})")
                return False, issues

            if record.prior_record_hash != prior_hash:
                issues.append(
                    f"Line {line_no}: prior_record_hash mismatch "
                    f"(expected {prior_hash}, got {record.prior_record_hash})"
                )

            recomputed = compute_record_hash(record)
            if recomputed != record.record_hash:
                issues.append(
                    f"Line {line_no}: record_hash mismatch "
                    f"(recomputed {recomputed}, stored {record.record_hash})"
                )

            prior_hash = record.record_hash

    return (len(issues) == 0), issues


class AuditLogger:
    """Append-only, hash-chained JSONL writer.

    Usage::

        logger = AuditLogger("/path/to/audit.jsonl")
        record = logger.append(
            record_id="ADR-1",
            pair_id="H-1:CVE-2025-12345",
            window_id="W-1",
            decision_type="schedule",
            weights_version="w-2026Q2-v1",
            data_feed_versions={"nvd": "2026-05-26", "epss": "2026-05-26"},
            framework_version="paper1-0.1.0",
            created_at=utc_now(),
        )

    The logger automatically computes ``prior_record_hash`` from its
    cached last hash (or the genesis hash) and ``record_hash`` from the
    canonical payload of the record being appended.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._last_hash: str | None = None
        if self._path.exists():
            self._last_hash = self._scan_last_hash()

    @property
    def path(self) -> Path:
        return self._path

    def last_hash(self) -> str:
        """Return the most-recently-appended record's hash, or genesis hash."""
        return self._last_hash if self._last_hash is not None else GENESIS_PRIOR_HASH

    def _scan_last_hash(self) -> str | None:
        last: str | None = None
        with open(self._path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                last = payload.get("record_hash")
        return last

    def append(self, **fields: Any) -> AuditDecisionRecord:
        """Build a record from `fields` and append it to the log.

        ``prior_record_hash`` and ``record_hash`` are computed
        automatically and must NOT be supplied by the caller.
        """
        if "prior_record_hash" in fields:
            raise ValueError("prior_record_hash is computed automatically")
        if "record_hash" in fields:
            raise ValueError("record_hash is computed automatically")

        prior = self.last_hash()
        # Construct with a placeholder hash that satisfies the regex; the
        # final record_hash is computed and substituted via model_copy
        # below. model_copy with `update=` does not re-run validators in
        # Pydantic v2, so the placeholder pattern is safe.
        temp = AuditDecisionRecord(
            **fields,
            prior_record_hash=prior,
            record_hash=GENESIS_PRIOR_HASH,
        )
        actual = compute_record_hash(temp)
        final = temp.model_copy(update={"record_hash": actual})

        write_jsonl(
            self._path,
            [final.model_dump(mode="json")],
            append=True,
        )
        self._last_hash = actual
        return final

    def iter_records(self) -> Iterator[AuditDecisionRecord]:
        """Yield each record in append order."""
        if not self._path.exists():
            return
        with open(self._path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                yield AuditDecisionRecord(**payload)

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Run hash-chain verification on the underlying file."""
        return verify_chain(self._path)
