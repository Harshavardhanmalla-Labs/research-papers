#!/usr/bin/env python3
"""CLI entry-point for Paper 2 — one-batch pilot runner (Step 6 smoke).

Thin wrapper around :func:`paper2_runtime.batch_runner.main`. Refuses every
batch except ``B-pilot-primary`` unless ``--allow-non-step6-batch`` is passed
(do not pass it during Step 6); refuses primary batches outright.
"""

from __future__ import annotations

import pathlib
import sys

# Make the in-repo `paper2_runtime` package importable when running from Make
# (pytest's `pythonpath = ["."]` does not apply here).
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from paper2_runtime.batch_runner import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
