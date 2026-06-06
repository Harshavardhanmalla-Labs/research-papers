# Paper 8 — Multi-Window-History Calibration

Does EWMA / trailing-mean smoothing reverse Paper 7's high-capacity
hazard for online recalibration of HygienePrio? Pre-registered answer:
**no — smoothing makes the hazard worse.**

**Target venue:** IEEE TNSM

## Headline findings (honest, pre-registered)

Cell-mean recovery ratios ($w \geq 2$):

| K   | lag1 (Paper 7) | trail3 | ewma3 |
|-----|----------------|--------|-------|
|  50 | +1.04          | (sim)  | +0.53 |
| 100 | +0.99          | (sim)  | −1.37 |
| 200 | −0.66          | (sim)  | −0.94 |

- **All 4 pre-registered hypotheses rejected.**
- Smoothing **degrades** moderate-capacity recovery and amplifies
  high-capacity hazard.
- Mechanism: under fast distributional shift, older calibration
  windows are misleading; bias term dominates variance reduction.
- Operational rule: use shortest possible history; turn off
  recalibration entirely at high capacity.

## Reproduce

From `paper8/`:
```bash
PYTHONPATH=src python3 src/run_multi_history.py    # 2,250-row sweep
PYTHONPATH=src python3 src/analyze.py              # H1–H4 + tables
PYTHONPATH=src python3 src/make_figures.py         # 2 figures
```

## Layout

```
paper8/
├── design/PAPER8_PROTOCOL.md
├── src/
│   ├── paper8/multi_history.py    # 5-strategy evaluator
│   ├── run_multi_history.py
│   ├── analyze.py
│   └── make_figures.py
├── results/primary_v1/
│   ├── multi_history_results.csv  # 2,250 rows
│   ├── cell_window_means.csv
│   ├── hypothesis_summary.json
│   └── run_manifest.json
└── submission/ieee/               # 7 pages, clean compile
    ├── main.tex / main.pdf
    ├── references.bib
    ├── sections/ (12 files)
    ├── tables/ (3 files)
    └── figures/ (2 PDFs)
```
