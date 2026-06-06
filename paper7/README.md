# Paper 7 — Rolling-History Online Calibration for Hygiene-Augmented Vulnerability Prioritization

Pre-registered evaluation of a deployable substitute for Paper 5's
offline-peek H3 calibration ablation. Tests whether one-window-lag
rolling-history grid search can rescue HygienePrio at Paper 6's
high-capacity collapse cells.

**Target venue:** IEEE TNSM

## Headline findings (honest, pre-registered)

- **K = 50 (canonical):** online recalibration recovers **92.5%** of
  the offline-peek W2 gain (+19.7 pp vs +21.3 pp ceiling). Cell-mean
  recovery ratio ρ = 1.04.
- **K = 100:** online recovers essentially all of the offline gain
  (ρ = 0.99) but the absolute floor remains low (W6 = 0.355).
- **K = 200:** online **harms** performance, losing −5.9 pp at W2 and
  −7.8 pp at W3. Cell-mean recovery ratio ρ = **−0.66**.
- **All three pre-registered hypotheses rejected** — the rejection
  pattern is the contribution.
- **H2 rejected in surprising direction:** online sometimes *beats*
  offline-peek (+3 pp at K=50, W5). Five-seed offline grid overfits;
  one-window lag acts as implicit regulariser.

## Operational summary

Deploy rolling-history online recalibration only when per-window
distributional shift is small relative to the lag. At high capacity,
keep fixed Paper-4 weights instead.

## Reproduce

From `paper7/`:
```bash
PYTHONPATH=src python3 src/run_online_calib.py    # 1,350-row sweep
PYTHONPATH=src python3 src/analyze.py             # H1–H3 outcomes + tables
PYTHONPATH=src python3 src/make_figures.py        # 2 figures
```

## Layout

```
paper7/
├── design/PAPER7_PROTOCOL.md          # pre-registration (locked 2026-06-04)
├── src/
│   ├── paper7/online_calib.py         # 3-strategy evaluator
│   ├── run_online_calib.py            # CLI entry
│   ├── analyze.py                     # H1-H3 + auto LaTeX tables
│   └── make_figures.py                # 2 figures
├── results/primary_v1/
│   ├── online_calib_results.csv       # 1,350 rows, frozen
│   ├── cell_window_means.csv          # per-cell-per-window aggregates
│   ├── hypothesis_summary.json        # H1-H3 outcomes
│   └── run_manifest.json
└── submission/ieee/                   # IEEE TNSM scaffold, 7 pages, clean compile
    ├── main.tex / main.pdf
    ├── references.bib
    ├── sections/ (12 files)
    ├── tables/ (3 files)
    └── figures/ (2 PDFs)
```

## Dependencies

Reuses Paper 4's `hygieneprio` package and Paper 5's `paper5.window_sim`
via `sys.path` injection. No code duplication.
