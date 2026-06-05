# Paper 11 — Threshold Sensitivity of Adaptive Change-Point Recalibration

Pre-registered sweep over τ ∈ {0.02, 0.03, 0.05, 0.075, 0.10} mapping
the H1/H2 Pareto curve for Paper 10's simple magnitude detector.

**Target venue:** IEEE TNSM

## Headline findings (honest, pre-registered)

- **H3 rejected (the central finding):** No τ in the grid satisfies both Paper 10 tolerances. K=50 cost is between −4.1 and −5.3 pp at every τ, always exceeding the −2.0 pp ceiling. **The simple magnitude detector cannot reach the joint feasible region.**
- **H1 substantively strengthened:** Worst per-window K=200 adaptive−fixed delta is uniformly 0.0 across the entire τ grid. The K=200 hazard-avoidance property is robust to threshold choice.
- **H2 and H4 protocol sign reversal:** Pre-registration predicted larger τ → more firing (H4) and more K=50 cost (H2). Data shows the opposite: ρ_H4 = −0.97 (p=0.005), ρ_H2 = +0.87. Larger τ requires larger shift to trigger and therefore fires less. Honest sign-error rejection.

## Operational rule

At fixed capacity in the studied ranges, the static rule (K ≤ 100 → lag1; K ≥ 200 → fixed) is sufficient. Adaptive switching adds operational complexity without reaching Paper 10's joint tolerance region. Richer detectors (capacity-aware τ, CUSUM, Bayesian) are required for the feasible region.

## Reproduce

```bash
PYTHONPATH=src python3 src/run_tau_sweep.py     # 11,250-row sweep
PYTHONPATH=src python3 src/analyze.py            # H1-H4 + auto tables
PYTHONPATH=src python3 src/make_figures.py       # Pareto + fire-vs-tau
```

## Layout

```
paper11/
├── design/PAPER11_PROTOCOL.md
├── src/
│   ├── paper11/tau_sweep.py
│   ├── run_tau_sweep.py
│   ├── analyze.py
│   └── make_figures.py
├── results/primary_v1/
│   ├── tau_sweep_results.csv      # 11,250 rows
│   ├── changepoint_log.csv        # 90 decisions
│   ├── per_tau_summary.csv
│   ├── cell_window_means.csv
│   ├── hypothesis_summary.json
│   └── run_manifest.json
└── submission/ieee/               # 6 pages, clean compile, 134 KB
```
