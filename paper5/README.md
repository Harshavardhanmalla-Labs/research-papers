# Paper 5 — Temporal Stability of Hygiene-Augmented Vulnerability Prioritization

This directory is the reproducibility artifact for Paper 5. It contains the
pre-registration protocol, the simulator, the frozen results CSV, the
recalibration ablation, the figures, and the IEEE TNSM submission LaTeX.

## Directory map

```
paper5/
├── design/
│   └── PAPER5_PROTOCOL.md          Pre-registered protocol (frozen 2026-06-04)
├── manuscript/
│   └── paper5_draft_v0.1.md        Internal markdown draft
├── src/
│   ├── paper5/
│   │   ├── window_sim.py           Per-window fleet-state evolution
│   │   ├── temporal_eval.py        Multi-window evaluation runner
│   │   └── recalib_ablation.py     H3 grid-search recalibration ablation
│   ├── run_temporal.py             CLI entry point for primary evaluation
│   └── make_figures.py             Generates fig1/fig2 from the frozen CSV
├── results/
│   └── primary_full_v1/
│       ├── temporal_results.csv         750 rows: 25 seeds × 6 windows × 5 methods
│       ├── recalibration_ablation.csv   6 rows: per-window fixed vs recalib P@50
│       ├── recalibration_summary.json   stop-rule outcome (H3 rejected)
│       └── run_manifest.json            seed lists, weights, k values
└── submission/ieee/
    ├── main.tex, references.bib    IEEEtran journal mode
    ├── sections/                   12 .tex files (00_abstract → 11_conclusion)
    ├── tables/                     tab_sim_params, tab_pk50_window, tab_recalibration
    └── figures/                    fig1_pk50_trajectory.pdf, fig2_stability.pdf
```

## Dependencies

- Python ≥ 3.9
- numpy, pandas, matplotlib
- Paper 4's `hygieneprio` package, located at `../paper4/src/hygieneprio`.
  The simulator imports it via a sys.path injection — no installation needed
  as long as the `paper4/` sibling directory is present.

## Reproducing the frozen results

From this directory:

```bash
# 1. Primary multi-window evaluation (750 rows)
PYTHONPATH=src python3 src/run_temporal.py

# 2. H3 recalibration ablation
PYTHONPATH=src python3 -m paper5.recalib_ablation

# 3. Figures
python3 src/make_figures.py
```

The runs are fully deterministic: same seeds → byte-identical CSVs.

## Reproducing the PDF

```bash
cd submission/ieee
tectonic main.tex   # or: pdflatex main && bibtex main && pdflatex main && pdflatex main
```

The current build produces an 8-page IEEE TNSM single-column journal PDF.

## Pre-registered hypotheses and outcomes

| ID | Hypothesis | Outcome |
|----|------------|---------|
| H1 | HygienePrio-full > EPSS-only at P@50, non-overlapping CIs, ≥ 4/6 windows | Supported (6/6) |
| H2 | Advantage largest at W1 and attenuates monotonically | Partially supported (own P@50 attenuates, gap to EPSS widens) |
| H3 | Per-window recalibration adds < 5 pp at P@50 | **Rejected** (max Δ = +21.3 pp at W2) |

## Headline numbers (mean P@50 across 25 evaluation seeds)

| Window | HygPrio-full | EPSS-only | HRS-only |
|--------|--------------|-----------|----------|
| 1 | **0.595** | 0.331 | 0.284 |
| 2 | **0.544** | 0.149 | 0.229 |
| 3 | **0.564** | 0.087 | 0.173 |
| 4 | **0.514** | 0.055 | 0.106 |
| 5 | **0.521** | 0.047 | 0.074 |
| 6 | **0.499** | 0.034 | 0.050 |

- HygienePrio-full > EPSS-only in **150 / 150** window-seed pairs
- Crossover (HRS-only overtakes EPSS-only): **W2**
- HygienePrio-vs-EPSS gap: **26.4 pp at W1 → 46.5 pp at W6**

## Scope and limitations

All results are bounded to the synthetic EEHDA fleet. The Hygiene Risk Score
appears in both the scorer and the ground-truth definition, creating a
structural advantage for HygienePrio variants that is acknowledged in the
manuscript's threats-to-validity section. External validation on real fleet
telemetry with longitudinal exploitation outcome data is required before any
deployment recommendation.

## Licence

MIT, consistent with the rest of the research-papers repository.
