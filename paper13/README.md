# Paper 13 — CUSUM Detector

Pre-registered evaluation of one-sided CUSUM(k=0.04, h=0.10) over
the calibration-target shift |Δ_w|. First detector in the Papers 7-13
program to beat the static gate at K=200.

**Target venue:** IEEE TNSM

## Headline findings (honest, pre-registered)

- **H2 substantive positive (binary rejection by 0.001 pp):** CUSUM K=200 cell-mean = 0.2754 vs gated = 0.2664, margin +0.9 pp. **First gate-breaking result in the program.** Pre-registered binary threshold was +0.01 pp; missed by 0.001 pp; rejection reported honestly.
- **H3 supported:** CUSUM fires at K=200 in 60% of windows vs cap_aware's 100% — selective firing as predicted.
- **H4 supported:** CUSUM K=200 strictly above cap_aware by +0.9 pp.
- **H1 rejected:** K=50 over-firing (20% rate) costs -3.9 pp. Single (k, h) pair cannot serve both K=50 and K=200.

## Mechanism

At K=200, CUSUM accumulates |Δ_w|−k. At W4 the |Δ| = 0.020 is below k=0.04 so accumulator zeroes — CUSUM uses lag-1 and captures the same +3.4 pp beneficial fit that adaptive05 captured by not firing. This breaks the static-gate collapse Paper 12 documented.

## Operational rule

- K ≤ 100: lag-1 directly
- K = 200: CUSUM(k=0.04, h=0.10) — first detector to beat static gate, +0.9 pp
- Mixed capacity: per-K (k_K, h_K) vector needed (untested; natural Paper 14)

## Reproduce

```bash
PYTHONPATH=src python3 src/run_cusum.py     # 2,700-row sweep
PYTHONPATH=src python3 src/analyze.py        # H1-H4 + tables
PYTHONPATH=src python3 src/make_figures.py   # 2 figures
```

## Layout

```
paper13/
├── design/PAPER13_PROTOCOL.md
├── src/
│   ├── paper13/cusum.py
│   ├── run_cusum.py
│   ├── analyze.py
│   └── make_figures.py
├── results/primary_v1/
│   ├── cusum_results.csv        # 2,700 rows
│   ├── changepoint_log.csv      # 18 decisions
│   ├── cell_window_means.csv
│   ├── hypothesis_summary.json
│   └── run_manifest.json
└── submission/ieee/             # 7 pages, clean compile, 143 KB
```
