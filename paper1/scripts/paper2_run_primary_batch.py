#!/usr/bin/env python3
"""CLI entry-point for Paper 2 — Step 8 primary batch runner.

Auto-selects ``--profile primary`` from any ``B-primary-*`` batch id and
requires ``--allow-step8-batch`` to actually launch. Refuses pilot batches,
smoke batches, calibration/learned cells, and any ``n != 30``.
"""

from __future__ import annotations

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from paper2_runtime.batch_runner import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
