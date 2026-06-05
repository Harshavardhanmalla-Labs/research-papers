"""CLI entry for Paper 10 adaptive recalibration evaluation."""
from __future__ import annotations
from pathlib import Path
from paper10.adaptive import run


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "results" / "primary_v1"
    run(output_dir=out)


if __name__ == "__main__":
    main()
