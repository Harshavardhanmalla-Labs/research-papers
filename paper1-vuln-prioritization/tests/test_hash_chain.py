"""Audit hash-chain tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from paper1.audit.hash_chain import (
    GENESIS_PRIOR_HASH,
    AuditLogger,
    compute_record_hash,
    verify_chain,
)
from paper1.audit.schema import AuditDecisionRecord


def _strip_internal_fields(kwargs: dict) -> dict:
    """Append() will compute prior_record_hash and record_hash itself."""
    out = dict(kwargs)
    out.pop("prior_record_hash", None)
    out.pop("record_hash", None)
    return out


def test_append_two_records_verify_chain_true(
    tmp_path: Path, sample_score_kwargs, sample_accept_risk_kwargs
):
    logger = AuditLogger(tmp_path / "audit.jsonl")
    r1 = logger.append(**_strip_internal_fields(sample_score_kwargs))
    r2 = logger.append(**_strip_internal_fields(sample_accept_risk_kwargs))

    assert r1.prior_record_hash == GENESIS_PRIOR_HASH
    assert r2.prior_record_hash == r1.record_hash
    ok, issues = logger.verify_chain()
    assert ok, issues


def test_last_hash_returns_latest(tmp_path: Path, sample_score_kwargs):
    logger = AuditLogger(tmp_path / "audit.jsonl")
    assert logger.last_hash() == GENESIS_PRIOR_HASH
    r = logger.append(**_strip_internal_fields(sample_score_kwargs))
    assert logger.last_hash() == r.record_hash


def test_tampered_record_breaks_chain(tmp_path: Path, sample_score_kwargs, sample_accept_risk_kwargs):
    path = tmp_path / "audit.jsonl"
    logger = AuditLogger(path)
    logger.append(**_strip_internal_fields(sample_score_kwargs))
    logger.append(**_strip_internal_fields(sample_accept_risk_kwargs))

    # Tamper with the first record's pair_id.
    lines = path.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    first["pair_id"] = "TAMPERED"
    lines[0] = json.dumps(first, sort_keys=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    ok, issues = verify_chain(path)
    assert not ok
    assert any("record_hash mismatch" in i for i in issues)


def test_tampered_field_breaks_record_self_hash(tmp_path: Path, sample_score_kwargs):
    path = tmp_path / "audit.jsonl"
    logger = AuditLogger(path)
    logger.append(**_strip_internal_fields(sample_score_kwargs))

    # Tamper with the priority score; record_hash should now mismatch.
    line = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    line["priority_score"] = 999.99
    path.write_text(json.dumps(line, sort_keys=True) + "\n", encoding="utf-8")

    ok, issues = verify_chain(path)
    assert not ok
    assert any("record_hash mismatch" in i for i in issues)


def test_caller_cannot_supply_record_hash(tmp_path: Path, sample_score_kwargs):
    logger = AuditLogger(tmp_path / "audit.jsonl")
    with pytest.raises(ValueError):
        logger.append(**sample_score_kwargs, record_hash="0" * 64)


def test_caller_cannot_supply_prior_record_hash(tmp_path: Path, sample_score_kwargs):
    logger = AuditLogger(tmp_path / "audit.jsonl")
    with pytest.raises(ValueError):
        logger.append(
            **_strip_internal_fields(sample_score_kwargs),
            prior_record_hash="0" * 64,
        )


def test_iter_records_in_append_order(
    tmp_path: Path, sample_score_kwargs, sample_accept_risk_kwargs
):
    logger = AuditLogger(tmp_path / "audit.jsonl")
    r1 = logger.append(**_strip_internal_fields(sample_score_kwargs))
    r2 = logger.append(**_strip_internal_fields(sample_accept_risk_kwargs))

    records = list(logger.iter_records())
    assert len(records) == 2
    assert records[0].record_id == r1.record_id
    assert records[1].record_id == r2.record_id


def test_compute_record_hash_excludes_record_hash(sample_score_kwargs):
    kwargs = dict(sample_score_kwargs)
    kwargs["prior_record_hash"] = GENESIS_PRIOR_HASH
    record_a = AuditDecisionRecord(**kwargs, record_hash="0" * 64)
    record_b = AuditDecisionRecord(**kwargs, record_hash="f" * 64)
    # Different record_hash but everything else identical → same payload hash.
    assert compute_record_hash(record_a) == compute_record_hash(record_b)


def test_compute_record_hash_includes_prior_record_hash(sample_score_kwargs):
    kwargs = dict(sample_score_kwargs)
    a = AuditDecisionRecord(
        **kwargs, prior_record_hash="0" * 64, record_hash="0" * 64
    )
    b = AuditDecisionRecord(
        **kwargs, prior_record_hash="1" + "0" * 63, record_hash="0" * 64
    )
    assert compute_record_hash(a) != compute_record_hash(b)


def test_logger_resumes_from_existing_file(
    tmp_path: Path, sample_score_kwargs, sample_accept_risk_kwargs
):
    path = tmp_path / "audit.jsonl"
    logger1 = AuditLogger(path)
    r1 = logger1.append(**_strip_internal_fields(sample_score_kwargs))

    # Re-open via a fresh AuditLogger; it should pick up the last hash.
    logger2 = AuditLogger(path)
    assert logger2.last_hash() == r1.record_hash
    r2 = logger2.append(**_strip_internal_fields(sample_accept_risk_kwargs))
    assert r2.prior_record_hash == r1.record_hash

    ok, issues = verify_chain(path)
    assert ok, issues


def test_accept_risk_record_in_chain_requires_risk_fields(
    tmp_path: Path, sample_accept_risk_kwargs
):
    logger = AuditLogger(tmp_path / "audit.jsonl")
    bad = _strip_internal_fields(sample_accept_risk_kwargs)
    bad.pop("risk_acceptance_reason")
    with pytest.raises(Exception):  # ValidationError wrapped by pydantic
        logger.append(**bad)


def test_verify_chain_missing_file_returns_false(tmp_path: Path):
    ok, issues = verify_chain(tmp_path / "nope.jsonl")
    assert not ok
    assert issues
