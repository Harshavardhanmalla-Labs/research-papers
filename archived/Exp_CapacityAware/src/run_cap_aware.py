"""CLI entry for Paper 12 capacity-aware sweep."""
from __future__ import annotations
from pathlib import Path
from paper12.cap_aware import run


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "results" / "primary_v1"
    run(output_dir=out)


if __name__ == "__main__":
    main()
