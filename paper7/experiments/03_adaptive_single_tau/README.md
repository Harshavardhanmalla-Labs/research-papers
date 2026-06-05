# Paper 10 — Change-Point-Aware Adaptive Recalibration

Pre-registered evaluation of the simplest adaptive calibration
procedure (one-threshold magnitude test on calibration-target shift)
against Paper 7's lag-1 baseline, Paper 8's smoothers (by implication),
a static capacity-conditional gate, and the offline-peek ceiling.

**Target venue:** IEEE TNSM

## Headline findings (honest, pre-registered)

- **H1 supported:** at K=200, adaptive ≥ fixed at every w. **First procedure in the Papers 7-8-10 sequence that avoids the K=200 hazard.** Cell-mean delta +0.7 pp.
- **H4 supported:** adaptive marginally beats static capacity gate by +0.7 pp at K=200.
- **H2 rejected:** at K=50 adaptive falls -5.3 pp below lag-1. Procedure trades moderate-capacity recovery for high-capacity safety.
- **H3 rejected:** firing fraction (60%, 40%, 80% at K=50, 100, 200) not monotone in K; Spearman ρ=0.5. Capacity is a proxy, not the cause.

## Operational rule

Deployable. For stable known capacity: use the static gate (simpler, almost as good). For variable capacity across deployment cycles: use adaptive switching.

## Reproduce

```bash
PYTHONPATH=src python3 src/run_adaptive.py
PYTHONPATH=src python3 src/analyze.py
PYTHONPATH=src python3 src/make_figures.py
```

## Layout

```
paper10/
├── design/PAPER10_PROTOCOL.md
├── src/
│   ├── paper10/adaptive.py
│   ├── run_adaptive.py
│   ├── analyze.py
│   └── make_figures.py
├── results/primary_v1/
│   ├── adaptive_results.csv         # 2,250 rows
│   ├── changepoint_log.csv          # 18 detector decisions
│   ├── cell_window_means.csv
│   ├── hypothesis_summary.json
│   └── run_manifest.json
└── submission/ieee/                 # 7 pages, clean compile, 137 KB
```
