"""CLI entry point: run the Paper 5 multi-window evaluation and freeze results.

Usage (from paper5/ with PYTHONPATH=src):
    python -m paper5.run_temporal
"""

from __future__ import annotations

from pathlib import Path

from paper5.temporal_eval import run_temporal_evaluation


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "results" / "primary_full_v1"
    run_temporal_evaluation(output_dir=out)


if __name__ == "__main__":
    main()
