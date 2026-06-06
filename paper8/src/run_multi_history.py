"""CLI entry for Paper 8 multi-history calibration evaluation."""
from __future__ import annotations
from pathlib import Path
from paper8.multi_history import run


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "results" / "primary_v1"
    run(output_dir=out)


if __name__ == "__main__":
    main()
