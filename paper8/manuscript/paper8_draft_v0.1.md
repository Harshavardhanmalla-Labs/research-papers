# Multi-Window-History Calibration: Does Smoothing Reverse the High-Capacity Hazard of Lag-1 Online Recalibration?

**Authors:** Harshavardhan Malla, Independent Researcher
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**Date:** June 2026
**Status:** Draft v0.1

---

## Abstract

Paper 7 found that lag-1 rolling-history online recalibration of the HygienePrio scorer recovers the offline-peek calibration ceiling at moderate capacity (per-cell recovery ratio ρ ∈ {1.04, 0.99} at K ∈ {50, 100}, λ = 3) but *harms* performance at K = 200 (ρ = −0.66). Paper 7 named multi-window-history smoothing as the natural candidate fix. This paper evaluates that fix in a pre-registered 2,250-row five-strategy comparison: **fixed** (Paper 4 weights), **lag1** (Paper 7 baseline), **trail3** (equal-weight 3-window trailing mean), **ewma3** (exponentially-weighted 3-window mean, α = 0.6), and **offline** (Paper 7 ceiling).

**All four pre-registered hypotheses are rejected, and the direction of rejection is the contribution.** Multi-window smoothing does *not* reverse the high-capacity hazard — it makes the hazard substantially worse. At K = 100, EWMA-3's cell-mean recovery ratio is **−1.37** (versus lag-1's +0.99); at K = 200 it is **−0.94** (versus lag-1's −0.66); at K = 50 EWMA-3 also underperforms lag-1 (ρ = 0.53 versus 1.04).

The mechanism is the inverse of the naive smoothing-helps intuition. At high capacity the fleet's distribution at window w has shifted substantially from windows w−3, w−2, w−1; weighting all three past windows in the calibration target pulls the selected weights *further* from the appropriate-for-window-w optimum, not closer to it. The hazard is monotone in history length: less history is better when the rate of distributional change is fast.

The operational recommendation that emerges is sharper than Paper 7's: deployable online recalibration in this setting should use the shortest possible history (lag-1 at most) and should be turned off entirely at high capacity. Future work is needed on more sophisticated adaptive procedures (change-point detection, Bayesian update with forgetting factor) that can identify when smoothing is locally appropriate.

All results are bounded to the synthetic EEHDA evaluation context.

**Keywords:** vulnerability prioritization; online calibration; EWMA; trailing-mean; smoothing; high-capacity hazard; pre-registration; reproducibility.

---

The full submission manuscript is at `submission/ieee/main.tex` (compiles to 7 pages via tectonic).
The pre-registration protocol is at `design/PAPER8_PROTOCOL.md`.
Frozen results: `results/primary_v1/multi_history_results.csv` (2,250 rows).
