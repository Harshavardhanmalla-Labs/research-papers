# Paper 12 — Pre-Registration Protocol

**Working title:** Capacity-Aware Threshold for Adaptive Change-Point
Recalibration: Can a Per-K $\tau$ Reach the Joint Feasibility Region?

**Author:** Harshavardhan Malla
**Target venue:** IEEE TNSM
**Date locked:** 2026-06-05 (before any capacity-aware-τ result was inspected)
**Builds on:** Paper 11 (τ sweep, simple detector cannot reach feasible region),
Paper 10 (adaptive detector at single τ), Paper 7 (lag-1 baseline).

---

## 1. Motivation

Paper 11 swept $\tau \in \{0.02, \ldots, 0.10\}$ and found that no
single τ in the grid satisfies both Paper 10 pre-registered tolerances
(worst K=200 ≥ -0.01 AND cell-mean K=50 ≥ -0.02). The K=50 cost
was uniformly ≤ -4 pp, missing the -2 pp ceiling at every τ.

Paper 11's discussion identified three richer detector families that
could in principle reach the feasible region; capacity-aware
thresholding is the simplest of them and requires only that the
deployment know the operating capacity. This paper tests whether a
single locked-before-evaluation per-K τ vector can reach the feasibility
region.

## 2. The pre-registered τ vector

The intuition is operational:
- At K=50, lag-1 recalibration is beneficial (Paper 7: ρ ≈ 1.0). A
  large τ_50 keeps the detector quiet so lag-1 is used most of the time.
- At K=200, lag-1 recalibration harms (Paper 7: ρ ≈ -0.66). A small
  τ_200 makes the detector fire often and revert to fixed.
- At K=100, the regime is intermediate. A middle τ_100 splits the
  difference.

Pre-registered values:
- **τ_50 = 0.20** (twice Paper 11's largest sweep value)
- **τ_100 = 0.05** (Paper 10 default, midpoint of Paper 11 grid)
- **τ_200 = 0.02** (Paper 11's smallest sweep value)

These values are locked before any capacity-aware-detector P@50 is
inspected. They are chosen by inspection of Paper 11's per-K |Δ_w|
distributions in the published cp_log only — no peeking at evaluation-seed
P@50 values for the capacity-aware strategy.

## 3. Strategies

Six strategies at every (cell, window):
- `fixed` — Paper 4 weights
- `lag1` — Paper 7 baseline
- `adaptive05` — Paper 10 single-τ adaptive at τ=0.05 (control)
- `cap_aware` — adaptive with τ_K as above
- `gated` — static (K≤100→lag1, K≥200→fixed)
- `offline` — Paper 7 ceiling

## 4. Pre-registered hypotheses

| ID | Statement | Decision rule |
|----|-----------|---------------|
| H1 | `cap_aware` reaches the joint feasibility region: worst K=200 ≥ -0.01 AND cell-mean K=50 ≥ -0.02 AND cell-mean K=100 ≥ -0.02. | Supported if all three tolerances are met. |
| H2 | `cap_aware` ≥ `adaptive05` at every (K, w≥2) cell-mean (within +0.01 tolerance for noise). | Supported if no cell-window fails. |
| H3 | `cap_aware` fire fraction is monotone non-increasing in K (K=50 fires most, K=200 fires least). Spearman ≤ -0.8. | Supported if rho ≤ -0.8 across the K=50, 100, 200 fire fractions. *Note: protocol predicts higher firing at SMALL K because lag-1 is preserved by large τ_50. The fire fraction = fraction of windows where lag-1 USED would imply higher K=50; but since the detector here fires == "use fixed", the protocol says K=50 fires LEAST (smallest fire fraction) because τ_50 is large.* |
| H4 | `cap_aware` cell-mean P@50 at K=200 ≥ `gated` cell-mean by ≥ +0.01. | Supported if delta ≥ 0.01. |

Reading H3 carefully: "fire" = detector fires = revert to fixed.
With large τ_50, |Δ_w| rarely crosses 0.20, so fire fraction is LOW
at K=50. With small τ_200, |Δ_w| easily crosses 0.02, so fire is HIGH
at K=200. Monotonicity: as K increases, fire fraction increases.
Spearman(K, fire_frac) should be ≥ +0.8 (not -0.8 as the protocol's
verbal description first stated — correcting here before evaluation).

**Corrected H3:** Spearman(K, fire_frac) ≥ +0.8.

**Stop rules:** If H1 is rejected, the abstract leads with "the
capacity-aware approach also cannot reach the feasibility region"
before the discussion is drafted.

## 5. Cell grid

K ∈ {50, 100, 200}, λ = 3, W = 6, 25 evaluation seeds, 5 calibration
seeds, 6 strategies. Total rows: 3 × 6 × 25 × 6 = **2,700**.

## 6. Out of scope

- τ_K values other than the pre-registered ones.
- Per-window τ adaptation.
- CUSUM and Bayesian detectors.
- Real fleet data.

Signed: Harshavardhan Malla, 2026-06-05.
