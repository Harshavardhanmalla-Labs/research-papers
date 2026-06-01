"""Tests for paper2_runtime.freeze_invariant (F7).

These tests do NOT shell out to `make verify-primary-freeze`. They construct
:class:`FreezeCheck` instances directly via the public helpers' ``check=``
parameter so that no expensive subprocess runs in unit tests.
"""

from __future__ import annotations

import json

import pytest

from paper2_runtime.freeze_invariant import (
    FORBIDDEN_PAPER1_PATHS,
    FreezeCheck,
    FreezeInvariantContext,
    Paper1FreezeInvariantViolation,
    sha256_file,
    write_freeze_witness_after,
    write_freeze_witness_before,
)

OK_CHECK = FreezeCheck(exit_code=0, stdout_tail="freeze verification: OK", status="OK")
FAIL_CHECK = FreezeCheck(exit_code=3, stdout_tail="freeze verification: FAIL", status="FAIL")


def test_sha256_file_round_trip(tmp_path):
    p = tmp_path / "a.bin"
    p.write_bytes(b"hello")
    assert sha256_file(p) == sha256_file(p)  # deterministic


def test_writes_all_four_witness_files_on_success(tmp_path, monkeypatch):
    out = tmp_path / "batches" / "B-test"
    before = write_freeze_witness_before("B-test", ["c1", "c2"], out, check=OK_CHECK)
    result = write_freeze_witness_after("B-test", ["c1", "c2"], out, before, check=OK_CHECK)
    assert (out / "freeze_witness_before.json").exists()
    assert (out / "freeze_witness_after.json").exists()
    assert (out / "freeze_invariant_result.json").exists()
    assert (out / "freeze_invariant_result.md").exists()
    assert result.status == "OK"


def test_fails_if_before_status_not_ok(tmp_path):
    out = tmp_path / "B-bad-before"
    ctx = FreezeInvariantContext("B-bad-before", ["c1"], out)
    # Pre-flight FreezeCheck FAIL would normally come from the subprocess; here
    # we exercise the context manager's failure path by direct construction.
    before = write_freeze_witness_before("B-bad-before", ["c1"], out, check=FAIL_CHECK)
    assert before.status == "FAIL"
    # write_freeze_witness_after then records that and the assertion fails.
    result = write_freeze_witness_after("B-bad-before", ["c1"], out, before, check=OK_CHECK)
    assert result.status == "FAIL"
    assert "before_status_ok" in (result.failure_reason or "")
    del ctx


def test_fails_if_manifest_hash_changes(tmp_path):
    out = tmp_path / "B-hash-mismatch"
    write_freeze_witness_before("B-hash-mismatch", ["c1"], out, check=OK_CHECK)
    # Tamper with the before-witness SHA to simulate post-run drift.
    before_path = out / "freeze_witness_before.json"
    payload = json.loads(before_path.read_text())
    payload["paper1_freeze_manifest_sha256"] = "0" * 64  # mismatched
    before_path.write_text(json.dumps(payload, indent=2))
    # Re-construct an in-memory witness with the new SHA so the after-call sees the mismatch.
    from paper2_runtime.freeze_invariant import FreezeWitness
    before_obj = FreezeWitness(**{**payload})
    result = write_freeze_witness_after("B-hash-mismatch", ["c1"], out, before_obj, check=OK_CHECK)
    assert result.status == "FAIL"
    assert "manifest_sha_equal" in (result.failure_reason or "")


def test_before_after_sha_preserved_when_invariant_holds(tmp_path):
    out = tmp_path / "B-sha-ok"
    before = write_freeze_witness_before("B-sha-ok", ["c1"], out, check=OK_CHECK)
    result = write_freeze_witness_after("B-sha-ok", ["c1"], out, before, check=OK_CHECK)
    assert result.assertions["manifest_sha_equal"]
    payload_before = json.loads((out / "freeze_witness_before.json").read_text())
    payload_after = json.loads((out / "freeze_witness_after.json").read_text())
    assert payload_before["paper1_freeze_manifest_sha256"] == payload_after["paper1_freeze_manifest_sha256"]


def test_refuses_paper1_output_dir(tmp_path):
    # Output dirs whose path segments coincide with forbidden Paper-1 territory
    # must be rejected.
    for forbidden in FORBIDDEN_PAPER1_PATHS:
        bad_dir = tmp_path.joinpath(forbidden.rstrip("/"))
        with pytest.raises(ValueError):
            write_freeze_witness_before("B-bad-dir", ["c1"], bad_dir, check=OK_CHECK)


def test_context_manager_marks_failed_batch_invalid(tmp_path):
    """Simulate K6 by tampering with the before-witness mid-batch."""
    out = tmp_path / "B-ctx-fail"
    # We bypass the real verify command via skip_verify=True for the test's CI cost.
    ctx = FreezeInvariantContext("B-ctx-fail", ["c1"], out, skip_verify=True)
    with pytest.raises(Paper1FreezeInvariantViolation):
        with ctx:
            # Mutate the before-witness to a different SHA so the after-assertion fails.
            payload_path = out / "freeze_witness_before.json"
            payload = json.loads(payload_path.read_text())
            payload["paper1_freeze_manifest_sha256"] = "0" * 64
            payload_path.write_text(json.dumps(payload, indent=2))
            # Mutate the in-memory FreezeWitness too so the post-run sees the bad SHA.
            from dataclasses import replace
            ctx.before_witness = replace(ctx.before_witness, paper1_freeze_manifest_sha256="0" * 64)
    assert ctx.result is not None
    assert ctx.result.status == "FAIL"


def test_does_not_invoke_freeze_primary(tmp_path):
    """The freeze_invariant module must never `make freeze-primary`."""
    import pathlib

    src_path = pathlib.Path(__file__).resolve().parents[1] / "paper2_runtime" / "freeze_invariant.py"
    text = src_path.read_text()
    assert "freeze-primary" not in text or text.count("freeze-primary") == 0, (
        "freeze_invariant.py must not invoke `make freeze-primary`"
    )
    assert "inspect-primary --freeze" not in text
