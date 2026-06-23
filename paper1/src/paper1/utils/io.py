"""Atomic IO, JSON / JSONL helpers, and SHA-256 file checksums."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

__all__ = [
    "atomic_write_json",
    "compute_file_sha256",
    "read_json",
    "read_jsonl",
    "write_jsonl",
]


_CHUNK = 64 * 1024


def compute_file_sha256(path: str | os.PathLike[str]) -> str:
    """Stream a SHA-256 checksum of a file's bytes; returns lowercase hex."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(_CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def atomic_write_json(path: str | os.PathLike[str], payload: Any) -> None:
    """Write JSON atomically: temp file in same directory, then rename.

    Keys are sorted; output is UTF-8 with `\\n` line termination. `default=str`
    handles date/datetime by relying on caller to pre-serialize when needed.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=target.name + ".", suffix=".tmp", dir=target.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, sort_keys=True, indent=2, default=str)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, target)
    except Exception:
        # Clean up the temp file on any failure before the rename.
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def read_json(path: str | os.PathLike[str]) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_jsonl(
    path: str | os.PathLike[str],
    records: list[dict[str, Any]],
    append: bool = False,
) -> None:
    """Write or append records as one JSON object per line."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with open(target, mode, encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True, default=str))
            fh.write("\n")


def read_jsonl(path: str | os.PathLike[str]) -> Iterator[dict[str, Any]]:
    """Lazily yield each line of a JSONL file as a parsed object."""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)
