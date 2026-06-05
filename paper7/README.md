# Paper 7 — Online Recalibration for Hygiene-Augmented Vulnerability Prioritization

A **consolidated** pre-registered comparison of six deployable
recalibration procedures, evaluated on the EEHDA fleet:

| Exp | Procedure | Sub-directory |
|-----|-----------|---------------|
| E1 | Lag-1 online | `experiments/01_lag1_*` |
| E2 | Multi-window smoothing (EWMA-3, trail-3) | `experiments/02_smoothing/` |
| E3 | Single-τ adaptive (τ=0.05) | `experiments/03_adaptive_single_tau/` |
| E4 | τ sensitivity sweep (5 values) | `experiments/04_tau_sweep/` |
| E5 | Capacity-aware τ vector | `experiments/05_capacity_aware/` |
| E6 | One-sided CUSUM (k=0.04, h=0.10) | `experiments/06_cusum/` |

**Target venue:** IEEE TNSM (journal article, 9 pages, clean compile).

## Headline finding (cumulative across six experiments)

The deployable recalibration recipe is **capacity-conditional**:

- **K ≤ 100:** deploy lag-1 online recalibration (E1, ρ ≈ 1.0 vs offline ceiling).
- **K = 200:** deploy CUSUM (E6, +0.9 pp over the static gate — the only operationally meaningful gain over the gate in the whole program).
- **Mixed capacity:** per-K (k_K, h_K) CUSUM vector required (future work).

## Pre-registration

- Consolidated protocol: [`design/PAPER7_PROTOCOL.md`](design/PAPER7_PROTOCOL.md) — 27 hypotheses across 6 experiments
- Per-experiment protocols: `experiments/0X_*/PROTOCOL.md` or `experiments/0X_*/design/`

## Reproduce

```bash
# E1 lag-1
PYTHONPATH=experiments/01_lag1_src python3 \
  experiments/01_lag1_src/run_temporal.py

# E2 smoothing
PYTHONPATH=experiments/02_smoothing/src python3 \
  experiments/02_smoothing/src/run_multi_history.py

# E3 adaptive (single τ)
PYTHONPATH=experiments/03_adaptive_single_tau/src python3 \
  experiments/03_adaptive_single_tau/src/run_adaptive.py

# E4 τ sweep
PYTHONPATH=experiments/04_tau_sweep/src python3 \
  experiments/04_tau_sweep/src/run_tau_sweep.py

# E5 capacity-aware τ
PYTHONPATH=experiments/05_capacity_aware/src python3 \
  experiments/05_capacity_aware/src/run_cap_aware.py

# E6 CUSUM
PYTHONPATH=experiments/06_cusum/src python3 \
  experiments/06_cusum/src/run_cusum.py
```

## Layout

```
paper7/
├── design/PAPER7_PROTOCOL.md          # consolidated 27-hypothesis protocol
├── experiments/
│   ├── 01_lag1_*                      # E1 src + results
│   ├── 02_smoothing/                  # E2 full sub-project
│   ├── 03_adaptive_single_tau/        # E3 full sub-project
│   ├── 04_tau_sweep/                  # E4 full sub-project
│   ├── 05_capacity_aware/             # E5 full sub-project
│   └── 06_cusum/                      # E6 full sub-project
└── submission/ieee/                   # 9-page IEEE TNSM manuscript
    ├── main.tex / main.pdf
    ├── references.bib
    ├── sections/ (12 files)
    └── tables/ (3 files: experiment coverage, hypothesis ledger, summary)
```

## Frozen artifacts

22,500 P@50 rows across six experiments, plus per-experiment
change-point decision logs. All numerical claims in the manuscript
trace to the per-experiment frozen CSVs.
