"""Deterministic seed derivation.

Sub-seeds are derived from a master seed and a name using SHA-256 so that
two implementations on different machines produce identical sub-seeds for
identical (master_seed, name) inputs. Python's built-in `hash()` is not
used because its result is randomized per-process by default.
"""

from __future__ import annotations

import hashlib

import numpy as np

__all__ = ["derive_subseed", "derive_subseeds", "make_rng"]

# Use uint64 for downstream compatibility with numpy SeedSequence and PCG64.
_SUBSEED_BYTES = 8  # 64 bits


def derive_subseed(master_seed: int, name: str) -> int:
    """Derive a deterministic 64-bit unsigned sub-seed from (master, name)."""
    if not isinstance(master_seed, int):
        raise TypeError(f"master_seed must be int; got {type(master_seed).__name__}")
    if master_seed < 0:
        raise ValueError("master_seed must be non-negative")
    if not isinstance(name, str) or not name:
        raise ValueError("name must be a non-empty string")
    payload = f"{master_seed}|{name}".encode()
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:_SUBSEED_BYTES], byteorder="big", signed=False)


def derive_subseeds(master_seed: int, names: list[str]) -> dict[str, int]:
    """Derive a dict of named sub-seeds. Duplicate names raise."""
    seen: set[str] = set()
    out: dict[str, int] = {}
    for n in names:
        if n in seen:
            raise ValueError(f"Duplicate sub-seed name: {n!r}")
        seen.add(n)
        out[n] = derive_subseed(master_seed, n)
    return out


def make_rng(seed: int) -> np.random.Generator:
    """Return a numpy Generator seeded deterministically with PCG64."""
    if not isinstance(seed, int):
        raise TypeError(f"seed must be int; got {type(seed).__name__}")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    return np.random.Generator(np.random.PCG64(seed))
