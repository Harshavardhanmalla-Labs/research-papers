# Paper 6 — Pre-Registration Protocol

**Working title:** Capacity-Indexed Decay of Exploit-Likelihood Vulnerability
Prioritization: A Two-Dimensional Sweep over Remediation Capacity and CVE
Arrival Rate

**Authors:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**Date locked:** 2026-06-04 (before any sweep-result inspection)
**Builds on:** Paper 4 (HygienePrio scorer + EEHDA generator),
Paper 5 (multi-window simulator + per-window evaluation).

---

## 1. Motivation

Paper 5 documented that EPSS-only Precision@50 decays from 0.331 at W1 to
0.034 at W6 on a fixed-parameter simulation (K = 50 selected pairs per window,
λ = 3 Poisson new-CVE arrivals per window). That study did *not* address two
operationally critical questions:

- **RQ1.** How does the decay rate scale with remediation capacity K?
  Faster remediation should drain the high-EPSS tail faster.
- **RQ2.** How does new-CVE arrival rate λ replenish the high-EPSS tail?
  Above some critical (K, λ) ratio, decay should stall or reverse.

Both are needed before any external recommendation about EPSS deployment can
be made: an organisation with K = 200 and λ = 12 sits in a very different
regime than K = 25 / λ = 1, and Paper 5's single-cell result does not tell
them which.

## 2. Research questions

- **RQ1.** Does EPSS-only's per-window P@50 decay slope steepen monotonically
  as K increases at fixed λ?
- **RQ2.** Does EPSS-only's decay slope flatten monotonically as λ increases
  at fixed K?
- **RQ3.** Across the (K, λ) grid, is there a critical ratio K/λ at which
  EPSS-only no longer decays meaningfully (slope > −0.01 P@50/window)?
- **RQ4.** Does HygienePrio-full retain P@50 ≥ 0.40 at W6 across *all*
  (K, λ) cells in the sweep?

## 3. Hypotheses

| ID | Statement | Decision rule |
|----|-----------|---------------|
| H1 | EPSS-only mean P@50 decay slope is monotonically more negative as K increases at every fixed λ. | Supported if Spearman ρ between K and decay slope is ≤ −0.8 at every λ. |
| H2 | EPSS-only decay slope is monotonically less negative (closer to zero) as λ increases at every fixed K. | Supported if Spearman ρ between λ and slope is ≥ +0.8 at every K. |
| H3 | A critical ratio K/λ exists at which EPSS-only slope ≥ −0.01 P@50/window. | Reported descriptively; not a binary test. |
| H4 | HygienePrio-full retains W6 mean P@50 ≥ 0.40 across all 20 (K, λ) cells. | Supported if all 20 cell means ≥ 0.40. |

H1–H4 are locked before any sweep-result inspection. **Stop rules:**
- If H4 is rejected (any cell < 0.40), the paper reports the failure cells
  honestly and the abstract is rewritten to qualify the claim before
  framing remediation recommendations.
- If H1 or H2 has Spearman ρ in [−0.5, +0.5], we report the non-monotonicity
  as the headline finding rather than the predicted monotone trend.

## 4. Sweep grid

| Axis | Values |
|------|--------|
| Capacity K (pairs/window) | 10, 25, 50, 100, 200 |
| Arrival rate λ (Poisson mean) | 1, 3, 6, 12 |
| Windows W | 6 |
| Methods | HygienePrio-full, EPSS-only, HRS-only, CVSS-only, Random |
| Seeds | 25 (105–129; identical to Paper 5 evaluation set) |

Total cells: 5 × 4 = **20**. Total rows: 20 × 25 × 6 × 5 = **15,000**.

All other parameters inherit Paper 5's pre-registration verbatim (patch debt
reduction Δ = 0.15, EPSS random-walk σ = 0.02, telemetry drift = +0.08/window,
recovery = −0.30, KEV prevalence = 0.08, calibrated scorer + HRS weights).

## 5. Fleet-state evolution

Identical to Paper 5 §5.4: at each window, the top-K pairs selected by
HygienePrio-full drive the fleet evolution for *all* methods scored at
that window. This avoids non-identifiable counterfactual fleets across
methods. Within each (K, λ) cell, K is the selection capacity used.

## 6. Metrics

- **P@K** per (cell, seed, window, method), K ∈ {50, 100, 250}.
- **Decay slope**: ordinary least-squares slope of P@50 vs window index
  (1..6) per (cell, seed, method); aggregated as mean ± 95 % percentile
  bootstrap across seeds.
- **W6 retention**: mean P@50 at W6 per cell × method.

## 7. Statistical reporting

- 95 % percentile bootstrap CIs with 10,000 resamples for all cell-mean
  point estimates.
- No null-hypothesis significance tests; comparisons rely on CI overlap.
- Spearman ρ reported per fixed-λ slice (H1) and per fixed-K slice (H2).
- All numerical claims trace to `paper6/results/primary_sweep_v1/sweep_results.csv`.

## 8. Reproducibility

The sweep driver is `paper6/src/run_sweep.py`. From `paper6/`:
```
PYTHONPATH=src python3 src/run_sweep.py
```
The driver re-uses Paper 5's `paper5.window_sim` and Paper 4's
`hygieneprio` package via `sys.path` injection (no code copy). Determinism
is inherited from Paper 5's per-(seed, window) RNG seeding.

## 9. Out of scope

- Real fleet data: not used. All claims are bounded to the synthetic
  EEHDA evaluation context.
- Online weight relearning: studied separately (Paper 5 §H3 ablation;
  could be future work for Paper 7).
- Non-greedy multi-window optimisation: future work.

## 10. Author certification

I certify that the (K, λ) grid, hypotheses, decision rules, and stop rules
above were fixed before any sweep result was computed. Any deviation
discovered during execution will be reported in a "Pre-registration
deviations" subsection of the manuscript.

Signed: Harshavardhan Malla, 2026-06-04.
