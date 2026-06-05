# Paper 12 — Capacity-Aware Threshold Detector

Pre-registered evaluation of a per-K threshold vector τ_K = {50: 0.20,
100: 0.05, 200: 0.02}. Direct follow-up to Paper 11's negative
feasibility result.

**Target venue:** IEEE TNSM

## Headline findings (honest, pre-registered)

- **H1 supported (the breakthrough):** capacity-aware reaches the joint feasibility region — first procedure in Papers 7-12 sequence to do so. All three tolerances met.
- **H3 supported:** firing fraction perfectly monotone in K (0%, 40%, 100% at K=50, 100, 200; ρ=1.0).
- **H4 rejected:** cap_aware K=200 cell mean equals gated K=200 cell mean exactly (0.2664 each). The per-window detector collapses to the static gate at K=200.
- **H2 rejected at 1 cell-window:** K=200/W4 cap_aware fires (|Δ|=0.020 ≥ τ=0.02) while adaptive05 doesn't (cp_delta < 0.05). Single-window cost -3.4 pp.

## Substantive interpretation

Capacity-aware thresholding reaches the feasibility region by approximating
the static gate at the two capacity extremes:
- K=50: τ_50=0.20 never fires → cap_aware = lag1 exactly
- K=200: τ_200=0.02 always fires → cap_aware = fixed exactly
- K=100: 40% intervention rate, -0.4 pp vs lag1 (within noise)

The detector validates the static gate as feasible but does not improve on it.

## Operational rule

Deploy the static gate (K≤100→lag1, K≥200→fixed). The capacity-aware detector adds operational complexity without operationally meaningful gain. Richer detectors (CUSUM, Bayesian) are required if the gate is to be improved upon.

## Reproduce

```bash
PYTHONPATH=src python3 src/run_cap_aware.py     # 2,700-row sweep
PYTHONPATH=src python3 src/analyze.py            # H1-H4 + tables
PYTHONPATH=src python3 src/make_figures.py       # 2 figures
```

## Layout

```
paper12/
├── design/PAPER12_PROTOCOL.md
├── src/
│   ├── paper12/cap_aware.py
│   ├── run_cap_aware.py
│   ├── analyze.py
│   └── make_figures.py
├── results/primary_v1/
│   ├── cap_aware_results.csv     # 2,700 rows
│   ├── changepoint_log.csv       # 18 decisions
│   ├── cell_window_means.csv
│   ├── hypothesis_summary.json
│   └── run_manifest.json
└── submission/ieee/              # 7 pages, clean compile, 139 KB
```
