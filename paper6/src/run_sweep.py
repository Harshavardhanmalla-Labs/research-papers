"""CLI entry point for the Paper 6 sweep.

Usage (from paper6/):
    PYTHONPATH=src python3 src/run_sweep.py
"""

from __future__ import annotations

from pathlib import Path

from paper6.sweep_eval import run_sweep


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "results" / "primary_sweep_v1"
    run_sweep(output_dir=out)


if __name__ == "__main__":
    main()
