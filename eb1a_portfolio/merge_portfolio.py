#!/usr/bin/env python3
"""
merge_portfolio.py — Build EB1A_Research_Portfolio_Malla_2026.pdf

Merges: exhibit_cover.pdf + Papers 1, 2, 3, 4, 5, 6, 7, 8, 9

Usage:
    python3 eb1a_portfolio/merge_portfolio.py
    # (run from the Research Papers root directory)

Requires: pypdf (pip install pypdf)
"""

import sys
from pathlib import Path

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    print("ERROR: pypdf not installed. Run: pip install pypdf")
    sys.exit(1)

ROOT = Path(__file__).parent.parent  # Research Papers/

COMPONENTS = [
    (ROOT / "eb1a_portfolio" / "exhibit_cover.pdf",                                         "Cover"),
    (ROOT / "paper1-vuln-prioritization" / "paper" / "submission" / "ieee" / "main.pdf",   "Paper 1 — VulnPrio"),
    (ROOT / "paper1-vuln-prioritization" / "paper2" / "submission" / "cset" / "main.pdf",  "Paper 2 — CalibScore"),
    (ROOT / "paper3" / "submission" / "acm" / "main.pdf",                                  "Paper 3 — HygieneBench"),
    (ROOT / "paper4" / "submission" / "ieee" / "main.pdf",                                 "Paper 4 — HygienePrio"),
    (ROOT / "paper5" / "submission" / "ieee" / "main.pdf",                                 "Paper 5 — Temporal Stability"),
    (ROOT / "paper6" / "submission" / "ieee" / "main.pdf",                                 "Paper 6 — Capacity-Indexed Decay"),
    (ROOT / "paper7" / "submission" / "ieee" / "main.pdf",                                 "Paper 7 — Online Recalibration (Lag-1)"),
    (ROOT / "paper8" / "submission" / "ieee" / "main.pdf",                                 "Paper 8 — Multi-History Smoothing"),
    (ROOT / "paper9" / "submission" / "ieee" / "main.pdf",                                 "Paper 9 — Self-Trajectory Evaluation"),
    (ROOT / "paper10" / "submission" / "ieee" / "main.pdf",                                "Paper 10 — AutoHeal Self-Healing Framework"),
]

OUTPUT = ROOT / "eb1a_portfolio" / "EB1A_Research_Portfolio_Malla_2026.pdf"


def main() -> None:
    writer = PdfWriter()
    total_pages = 0

    for path, label in COMPONENTS:
        if not path.exists():
            print(f"  MISSING: {path}")
            print(f"    Run tectonic on the source .tex file first.")
            sys.exit(1)
        reader = PdfReader(str(path))
        n = len(reader.pages)
        print(f"  ✓ {label}: {n} pages  ({path.name})")
        for page in reader.pages:
            writer.add_page(page)
        total_pages += n

    with open(OUTPUT, "wb") as f:
        writer.write(f)

    size_kb = OUTPUT.stat().st_size / 1024
    print(f"\nMerged → {OUTPUT.name}")
    print(f"  {total_pages} pages · {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
