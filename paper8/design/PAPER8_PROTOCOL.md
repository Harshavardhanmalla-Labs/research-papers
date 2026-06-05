# Paper 8 — Pre-Registration Protocol

**Working title:** Multi-Window-History Calibration: Does Smoothing
Reverse the High-Capacity Hazard of Lag-1 Online Recalibration?

**Authors:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**Date locked:** 2026-06-04 (before any multi-history-calibration result was inspected)
**Builds on:** Paper 7 (lag-1 rolling-history calibration), Paper 6
(capacity sweep), Paper 5 (multi-window simulator), Paper 4 (scorer).

---

## 1. Motivation

Paper 7 evaluated lag-1 rolling-history online calibration and found:
- At $K = 50$, $\rho_{\text{recovery}} = 1.04$ (online matches offline-peek).
- At $K = 100$, $\rho_{\text{recovery}} = 0.99$ (online matches).
- At $K = 200$, $\rho_{\text{recovery}} = -0.66$ (online HARMS).

Paper 7 §11 explicitly named multi-window-history smoothing as the
candidate fix. This paper tests two operationally simple smoothing
schemes --- exponentially-weighted moving average (EWMA) and trailing
arithmetic mean --- and asks whether either reverses the $K = 200$
hazard without breaking the $K \in \{50, 100\}$ recovery.

## 2. Research questions

- **RQ1.** Does EWMA-3 (exponentially-weighted last 3 windows) reverse
  the lag-1 hazard at $K = 200$?
- **RQ2.** Does trailing-mean-3 (arithmetic mean of last 3 windows of
  calibration history) reverse the hazard?
- **RQ3.** Does smoothing degrade performance at $K = 50, 100$ where
  lag-1 already worked?
- **RQ4.** Is the choice between EWMA and trailing-mean a second-order
  decision (similar outcomes) or first-order (substantially different)?

## 3. Calibration strategies (locked)

Five strategies are compared at every (cell, window). At $w = 1$, all
strategies reduce to `fixed`. At $w \geq 2$:

| Tag | Strategy |
|-----|----------|
| `fixed` | Paper 4 weights, never refit |
| `lag1` | Grid-search on calib seeds at window $w-1$ (Paper 7 baseline) |
| `trail3` | Grid-search on calib seeds aggregated over windows $\max(1, w-3) \ldots w-1$ (P@50 averaged across windows in the trailing window) |
| `ewma3` | Same calibration windows as `trail3`, but with weights $w_i \propto \alpha^{i}$ where $i$ counts back from current window and $\alpha = 0.6$ |
| `offline` | Grid-search at window $w$ (Paper 7 offline-peek ceiling) |

Grid identical to Paper 7 (108 points).

## 4. Hypotheses

| ID | Statement | Decision rule |
|----|-----------|---------------|
| H1 | At $K = 200$, EWMA-3 mean P@50 $\geq$ fixed at every $w \geq 2$ (no hazard). | Supported if all six post-W1 (cell K=200, window) deltas $\Delta_{\text{ewma}-\text{fix}} \geq -0.01$. |
| H2 | At $K \in \{50, 100\}$, EWMA-3 mean P@50 within $\pm 2$ pp of lag-1 at every window (no smoothing penalty). | Supported if all (cell, window) $|\Delta_{\text{ewma}-\text{lag1}}| \leq 0.02$. |
| H3 | EWMA-3 and trailing-mean-3 produce P@50 within $\pm 2$ pp of each other at every cell-window (smoothing-strategy choice is second-order). | Supported if all (cell, window) $|\Delta_{\text{ewma}-\text{trail3}}| \leq 0.02$. |
| H4 | At $K = 200$, EWMA-3 recovery ratio $\bar\rho \geq 0.5$ (substantial offline-ceiling recovery achieved). | Supported if cell-mean recovery ratio across $w \geq 2$ $\geq 0.5$. |

**Stop rules:**
- If H1 is rejected, the abstract is rewritten to qualify the EWMA-rescue
  claim before drafting the discussion.
- If H2 is rejected, the paper reports that smoothing has a non-zero
  cost in the regimes where lag-1 worked, and the operational
  recommendation is qualified accordingly.

## 5. Cell grid

Three capacity levels at fixed $\lambda = 3$: $K \in \{50, 100, 200\}$.
Strategies: 5 (fixed, lag1, trail3, ewma3, offline).
Windows: 6. Eval seeds: 25 (105--129). Calib seeds: 5 (100--104).

Total rows: $3 \times 5 \times 6 \times 25 = 2{,}250$.

## 6. Metrics

- P@50 per (cell, seed, window, strategy).
- Per-(cell, window) deltas vs `fixed` and vs `lag1`.
- Recovery ratio $\bar\rho_K$ vs offline-peek ceiling.

## 7. Reporting

95\% percentile bootstrap CIs (10{,}000 resamples). No NHST. All claims
trace to `paper8/results/primary_v1/multi_history_results.csv`.

## 8. Reproducibility

From `paper8/`:
```
PYTHONPATH=src python3 src/run_multi_history.py
```
Reuses Paper 4 / 5 / 7 code via sys.path.

## 9. Out of scope

- Smoothing strategies beyond EWMA and trailing-mean (e.g., Kalman filter,
  Bayesian update) — future work.
- Sweeping $\lambda$ — held at 3 to control scope.
- Real fleet data — bounded to synthetic.

## 10. Author certification

Cell grid, strategies, hypotheses, decision rules, and stop rules were
fixed before any multi-history-calibration result was computed.

Signed: Harshavardhan Malla, 2026-06-04.
