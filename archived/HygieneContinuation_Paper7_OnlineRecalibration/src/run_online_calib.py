"""CLI entry point for the Paper 7 online-calibration evaluation.

Usage (from paper7/):
    PYTHONPATH=src python3 src/run_online_calib.py
"""
from __future__ import annotations
from pathlib import Path
from paper7.online_calib import run


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "results" / "primary_v1"
    run(output_dir=out)


if __name__ == "__main__":
    main()
