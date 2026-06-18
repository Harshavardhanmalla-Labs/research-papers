# Paper 11 — Pre-Registration Protocol

**Working title:** Threshold Sensitivity of Adaptive Change-Point
Recalibration: Mapping the H1/H2 Pareto Frontier Over τ

**Author:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**Date locked:** 2026-06-05 (before any τ-sweep result was computed)
**Builds on:** Paper 10 (adaptive change-point at fixed τ=0.05),
Paper 7 (lag-1 baseline), Paper 8 (smoothers falsified), Paper 4 (scorer).

---

## 1. Motivation

Paper 10's adaptive procedure used a single pre-registered threshold
τ = 0.05 and produced a mixed outcome: H1 supported (no hazard at
K = 200), H2 rejected (5.3 pp penalty at K = 50). Paper 10's
discussion (§8.3) argued the H2 cost is the principled price of H1
success and is parameterised by τ. A smaller τ should fire less,
shrinking the H2 penalty at moderate K but re-introducing some H1
hazard at K = 200; a larger τ should fire more, removing all H1
hazard but enlarging the H2 cost.

This paper tests that claim directly. We sweep τ over a
pre-registered grid and characterise the resulting H1/H2 Pareto curve.

## 2. Research questions

- **RQ1.** Is the H1 hazard (worst per-window adaptive−fixed delta at
  K = 200) monotone non-decreasing in τ?
- **RQ2.** Is the H2 penalty (cell-mean adaptive−lag1 at K = 50) monotone
  non-increasing in τ?
- **RQ3.** Does there exist a τ in the swept grid such that both H1 and
  H2 are simultaneously satisfied (i.e., a single operating point that
  passes the Paper 10 pre-registered tolerances)?
- **RQ4.** Is the firing fraction at every K monotone non-decreasing in τ?

## 3. τ sweep grid (locked)

τ ∈ {0.02, 0.03, 0.05, 0.075, 0.10}. The grid spans roughly an order
of magnitude with denser sampling at the small end (where H1 risk is
expected to appear). All other parameters inherit Paper 10's
protocol verbatim:
- Strategies: fixed, lag1, adaptive(τ), gated, offline
- K ∈ {50, 100, 200}, λ = 3, W = 6
- Calibration seeds 100–104; evaluation seeds 105–129
- Calibration grid identical to Paper 7/8/10 (108 points)
- Fleet evolution driven by fixed-weight HygienePrio-full

Total rows: 5 τ × 3 K × 5 strategies × 25 seeds × 6 windows = **11,250**.
Plus change-point decision log: 5 τ × 3 K × 6 W = 90 rows.

## 4. Pre-registered hypotheses

| ID | Statement | Decision rule |
|----|-----------|---------------|
| H1 | Worst per-window adaptive−fixed delta at K=200 is monotone non-decreasing in τ across the swept grid. | Supported if Spearman(τ, worst-delta) ≥ +0.8. |
| H2 | Cell-mean adaptive−lag1 at K=50 is monotone non-increasing in τ. | Supported if Spearman(τ, delta) ≤ −0.8. |
| H3 | At least one τ in the grid satisfies both: (a) worst K=200 per-window delta ≥ −0.01, AND (b) cell-mean K=50 adaptive−lag1 ≥ −0.02. | Supported if any τ passes both tests. |
| H4 | Cell-mean firing fraction (averaged over K) is monotone non-decreasing in τ. | Supported if Spearman(τ, mean-fire-frac) ≥ +0.8. |

**Stop rules:**
- If H3 is supported, the abstract leads with the operating-point
  recommendation; if rejected, the abstract leads with the
  unavoidable trade-off claim.
- If H1 or H2 monotonicity is rejected, the discussion characterises
  the non-monotonicity rather than rationalising it.

## 5. Reproducibility

```
PYTHONPATH=src python3 src/run_tau_sweep.py
PYTHONPATH=src python3 src/analyze.py
PYTHONPATH=src python3 src/make_figures.py
```

## 6. Out of scope

- τ values outside [0.02, 0.10] — extrapolation only.
- λ sweep — λ fixed at 3.
- Detector families other than the one-threshold magnitude test.
- Real fleet data.

## 7. Certification

Grid, hypotheses, decision rules, and stop rules locked before any
τ-sweep result was computed.

Signed: Harshavardhan Malla, 2026-06-05.
