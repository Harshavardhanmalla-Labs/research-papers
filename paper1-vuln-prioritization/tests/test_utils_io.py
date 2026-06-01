"""Atomic IO and checksum tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from paper1.utils.io import (
    atomic_write_json,
    compute_file_sha256,
    read_json,
    read_jsonl,
    write_jsonl,
)


def test_checksum_stable(tmp_path: Path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"hello world")
    a = compute_file_sha256(p)
    b = compute_file_sha256(p)
    assert a == b
    assert len(a) == 64
    # SHA-256("hello world")
    assert a == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"


def test_checksum_changes_after_mutation(tmp_path: Path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"hello")
    a = compute_file_sha256(p)
    p.write_bytes(b"world")
    b = compute_file_sha256(p)
    assert a != b


def test_atomic_write_json_roundtrip(tmp_path: Path):
    p = tmp_path / "subdir" / "config.json"
    payload = {"b": 2, "a": 1, "c": [3, 1, 2]}
    atomic_write_json(p, payload)
    assert p.exists()
    loaded = read_json(p)
    assert loaded == payload
    # File contents are sorted-key form.
    text = p.read_text(encoding="utf-8")
    assert text.index('"a"') < text.index('"b"') < text.index('"c"')


def test_atomic_write_no_temp_file_left_behind(tmp_path: Path):
    p = tmp_path / "f.json"
    atomic_write_json(p, {"x": 1})
    leftovers = [child for child in tmp_path.iterdir() if child.name != "f.json"]
    assert leftovers == []


def test_atomic_write_overwrites_existing(tmp_path: Path):
    p = tmp_path / "f.json"
    atomic_write_json(p, {"v": 1})
    atomic_write_json(p, {"v": 2})
    assert read_json(p) == {"v": 2}


def test_jsonl_write_then_read(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    records = [{"i": i, "name": f"r{i}"} for i in range(5)]
    write_jsonl(p, records)
    loaded = list(read_jsonl(p))
    assert loaded == records


def test_jsonl_append_mode(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    write_jsonl(p, [{"i": 0}])
    write_jsonl(p, [{"i": 1}, {"i": 2}], append=True)
    loaded = list(read_jsonl(p))
    assert loaded == [{"i": 0}, {"i": 1}, {"i": 2}]


def test_jsonl_skips_blank_lines(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    p.write_text('{"a": 1}\n\n{"a": 2}\n\n', encoding="utf-8")
    loaded = list(read_jsonl(p))
    assert loaded == [{"a": 1}, {"a": 2}]


def test_compute_file_sha256_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        compute_file_sha256(tmp_path / "does-not-exist")


def test_atomic_write_json_keys_are_sorted_recursively(tmp_path: Path):
    p = tmp_path / "f.json"
    payload = {"outer_b": {"inner_z": 1, "inner_a": 2}, "outer_a": 0}
    atomic_write_json(p, payload)
    text = p.read_text(encoding="utf-8")
    assert text.index('"inner_a"') < text.index('"inner_z"')
    assert text.index('"outer_a"') < text.index('"outer_b"')
    # Sanity: parse roundtrip is loss-free
    assert json.loads(text) == payload
