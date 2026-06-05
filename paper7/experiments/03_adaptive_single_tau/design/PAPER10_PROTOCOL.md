# Paper 10 — Pre-Registration Protocol

**Working title:** Change-Point-Aware Adaptive Recalibration for
Hygiene-Augmented Vulnerability Prioritization: Capacity-Conditional
Switching Between Fixed and Lag-1 Online Calibration

**Authors:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**Date locked:** 2026-06-05 (before any adaptive-calibration result was inspected)
**Builds on:** Paper 7 (lag-1 online), Paper 8 (smoothing falsified),
Paper 6 (capacity sweep), Paper 5 (multi-window), Paper 4 (scorer).

---

## 1. Motivation

Paper~7 found lag-1 online recalibration works at moderate capacity
($K \in \{50, 100\}$: $\rho \approx 1.0$) but harms at high capacity
($K = 200$: $\rho = -0.66$). Paper~8 falsified the natural fix
(multi-window smoothing): EWMA and trailing-mean degrade further.
Paper~8 explicitly named *adaptive procedures* --- change-point
detection plus capacity-conditional gating --- as the remaining
candidate.

This paper evaluates the simplest such adaptive procedure: monitor a
change-point statistic on the calibration-seed score stream and switch
between \textsf{lag1} (when the distribution is stable) and \textsf{fixed}
(when a change-point is detected) at each window. The intuition is:
when the rate of distributional change exceeds what lag-1 can track,
fall back to the Paper~4 fixed weights rather than fitting on the
mis-aligned previous-window state.

## 2. Research questions

- **RQ1.** Does adaptive switching reverse the lag-1 hazard at $K = 200$?
- **RQ2.** Does adaptive switching preserve lag-1's moderate-capacity
  recovery at $K \in \{50, 100\}$?
- **RQ3.** What fraction of windows does the change-point detector fire,
  and does that fraction scale monotonically with $K$?
- **RQ4.** Does adaptive switching outperform a static capacity-gated
  rule (lag-1 if $K \leq 100$, fixed if $K \geq 200$)?

## 3. Strategies (locked)

Five strategies at every (cell, window):

| Tag | Strategy |
|-----|----------|
| `fixed`   | Paper 4 weights, never refit |
| `lag1`    | Paper 7 baseline: grid-search on calib seeds at $w-1$ |
| `adaptive`| Lag-1 weights if change-point not detected at $w$; fixed weights otherwise |
| `gated`   | Lag-1 weights if $K \leq 100$; fixed if $K \geq 200$ (no detector) |
| `offline` | Paper 7 ceiling: grid-search at $w$ on calibration seeds |

## 4. Change-point detector (locked)

At window $w \geq 2$ and for the five calibration seeds:
1. Compute mean P@50 of the candidate lag-1-fit weights at the
   $w-1$ calibration state ($p_{w-1}^{\text{lag1-fit}}$).
2. Compute mean P@50 of the same lag-1-fit weights at the
   $w-2$ calibration state ($p_{w-2}^{\text{lag1-fit}}$); if $w = 2$,
   compare against $p_0$ defined as the fixed-weight Paper 4 baseline
   at the $w-1$ state.
3. If $|p_{w-1} - p_{w-2}| \geq \tau$, fire the change-point and
   switch to \textsf{fixed} for window $w$; otherwise use the lag-1
   weights.
4. Threshold $\tau = 0.05$ is pre-registered.

The detector is intentionally simple: a one-sample magnitude test on the
calibration-target shift. More sophisticated CUSUM / Bayesian online
change-point detectors are out of scope.

## 5. Hypotheses

| ID | Statement | Decision rule |
|----|-----------|---------------|
| H1 | At $K = 200$, `adaptive` $\geq$ `fixed` at every $w \geq 2$ (within $-0.01$). | Supported if no cell-window fails. |
| H2 | At $K \in \{50, 100\}$, `adaptive` within $\pm 0.02$ of `lag1` at every $w \geq 2$. | Supported if no cell-window fails. |
| H3 | Change-point firing fraction is monotone in $K$ (more fires at higher $K$). | Supported if $\mathrm{Spearman}(K, \mathrm{fire\_frac}) \geq +0.8$. |
| H4 | `adaptive` $\geq$ `gated` at $K = 200$, on cell mean P@50. | Supported if cell mean delta $\geq 0$. |

**Stop rules:**
- If H1 fails on $\geq 2$ cell-windows, the abstract is rewritten before
  the discussion is drafted.
- If H3 fails (no monotone firing), the adaptive procedure is
  characterised as ``effectively static'' and the headline is rephrased
  accordingly.

## 6. Cell grid

$K \in \{50, 100, 200\}$, $\lambda = 3$, six windows, 25 evaluation
seeds (105--129), 5 calibration seeds (100--104), 5 strategies. Total
rows: $3 \times 5 \times 25 \times 6 = 2{,}250$.

## 7. Metrics

- P@50 per (cell, seed, window, strategy).
- Change-point firing fraction per cell.
- Cell-mean deltas (`adaptive` $-$ `fixed`, `adaptive` $-$ `lag1`,
  `adaptive` $-$ `gated`).
- 95\% percentile bootstrap CIs (10{,}000 resamples).

## 8. Reproducibility

From `paper10/`:
```
PYTHONPATH=src python3 src/run_adaptive.py
```

## 9. Out of scope

CUSUM / Bayesian online change-point methods; sensitivity sweeps over
$\tau$; real fleet validation; sweeping $\lambda$.

## 10. Certification

Strategies, detector, threshold, hypotheses, and stop rules were
fixed before any adaptive-calibration result was computed.

Signed: Harshavardhan Malla, 2026-06-05.
