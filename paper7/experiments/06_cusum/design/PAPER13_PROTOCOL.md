# Paper 13 — Pre-Registration Protocol

**Working title:** CUSUM Detector for Adaptive Change-Point Recalibration:
Can Multi-Window Evidence Accumulation Break the Static-Gate Collapse?

**Author:** Harshavardhan Malla
**Target venue:** IEEE TNSM
**Date locked:** 2026-06-05 (before any CUSUM-detector P@50 was inspected)
**Builds on:** Paper 12 (capacity-aware τ, structurally equals static gate),
Paper 11 (single-τ infeasibility), Paper 10 (single-τ magnitude detector).

---

## 1. Motivation

Paper 12 showed that the capacity-aware threshold detector reaches the
joint feasibility region but its K=200 cell mean equals the static
gate's exactly because the small τ_200=0.02 fires at every K=200
window. The per-window detector collapses to the unconditional
revert-to-fixed gate at high capacity.

Paper 12 named CUSUM as the candidate to break this collapse: a
detector that accumulates evidence across windows can in principle
refrain from firing at single-window noise excursions (such as the
K=200 W4 |Δ|=0.020 case) and capture the lag-1 benefit at those
windows.

This paper evaluates a simple CUSUM detector with pre-registered
slack k and alarm threshold h, and tests whether it beats the static
gate's K=200 cell mean.

## 2. CUSUM detector

At each window w ≥ 2, maintain an accumulator C_w:

  C_1 = 0
  C_w = max(0, C_{w-1} + |Δ_w| - k)  for w ≥ 2

Fire if C_w ≥ h. After firing, reset C_w = 0 and continue from the
next window. The detector uses Paper 10's magnitude statistic
|Δ_w| (calibration-target shift) as the input.

**Pre-registered parameters:**
- k = 0.04 (slack; one-half the typical |Δ| at K=50 from Paper 11)
- h = 0.10 (alarm threshold; the Paper 11 largest single-τ that still
  failed feasibility)

The intuition: a single |Δ|=0.05 contributes 0.05−0.04 = 0.01 to the
accumulator and is unlikely to cross h=0.10. Two consecutive |Δ|=0.05
contribute 0.02 total and still don't fire. But sustained shifts —
e.g., three consecutive |Δ|=0.10 — accumulate to 0.18 well above h.

## 3. Strategies

Six strategies at every (cell, window):
- `fixed`        — Paper 4 weights
- `lag1`         — Paper 7 baseline
- `cap_aware`    — Paper 12 capacity-aware (control)
- `cusum`        — CUSUM(k=0.04, h=0.10) over |Δ_w|
- `gated`        — static rule (K≤100→lag1, K≥200→fixed)
- `offline`      — Paper 7 ceiling

## 4. Pre-registered hypotheses

| ID | Statement | Decision rule |
|----|-----------|---------------|
| H1 | CUSUM reaches the joint feasibility region: worst K=200 cusum-fix ≥ -0.01, cell-mean K=50 cusum-lag1 ≥ -0.02, cell-mean K=100 cusum-lag1 ≥ -0.02. | All three tolerances met. |
| H2 | CUSUM K=200 cell-mean P@50 ≥ gated K=200 cell-mean by +0.01. | Cell-mean delta ≥ 0.01. |
| H3 | CUSUM K=200 fires fewer times than cap_aware (selective firing). | CUSUM K=200 fire fraction strictly less than cap_aware's (1.0). |
| H4 | CUSUM cell-mean P@50 at K=200 ≥ adaptive05 (Paper 10) within 0.01 noise. | Cell-mean delta ≥ -0.01. |

**Stop rules:**
- If H2 is rejected, the abstract leads with "CUSUM also collapses to
  static gate" before discussion is drafted.
- If H1 is rejected, the abstract leads with "CUSUM cannot reach
  feasibility" — feasibility takes precedence over improvement claims.

## 5. Cell grid

K ∈ {50, 100, 200}, λ = 3, W = 6, 25 evaluation seeds, 5 calibration
seeds, 6 strategies. Total rows: **2,700**.

## 6. Out of scope

- (k, h) sensitivity sweep — future work.
- Two-sided CUSUM, EWMA-CUSUM, Bayesian online change-point.
- Real fleet data.

Signed: Harshavardhan Malla, 2026-06-05.
