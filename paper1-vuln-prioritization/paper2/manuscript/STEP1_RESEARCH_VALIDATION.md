<!--
Paper 2 — Step 1: Research Validation Report.
Internal planning document (skeptical go/no-go), NOT the manuscript and NOT for
submission. Contains no fabricated citations ([VERIFY] used for unconfirmed
sources). EB1A scoring here is internal planning meta, not language for the paper.
Paper 1 (../paper/, results/primary_full_v1/) is NOT touched by this work.
-->

# Paper 2 — Step 1: Research Validation Report

**Working title:** *Calibrated Vulnerability-Host Prioritization: Sensitivity and
Label-Robustness Analysis Using a Frozen Public-Sector-Shaped Benchmark*

**Status:** CONDITIONAL GO (three conditions in §18). **Prior topic killed:** the
"NIST 800-53 evidence-quality benchmark" was pivoted away from in Step 2.5 after
close April-2026 OSCAL/compliance-evidence prior art was found; it is not continued
here.

**Skeptical disclosure:** I proposed this direction in the prior step, so this
report deliberately over-weights weaknesses. Honest headline: a **legitimate but
moderate "analysis/results companion" to Paper 1**, with real incrementality risk
and a real chance the empirical answer is again neutral. It is **clearly stronger
than the killed compliance paper**, but it is **not** high-novelty, and its value
must **not** depend on a positive result.

---

## 1. Improved title options
1. *"Does Context Help? A Pre-Registered Robustness and Sensitivity Study of
   Calibrated Vulnerability-Host Prioritization Against EPSS/CVSS/KEV"* (recommended
   — leads with the falsifiable question + integrity).
2. "Calibration and Label Robustness in Capacity-Constrained Vulnerability
   Prioritization: A Frozen-Benchmark Analysis."
3. "When Calibrated Context-Aware Scoring Beats EPSS — and When It Doesn't: A
   Sensitivity Study on a Reproducible Public-Sector-Shaped Benchmark."
4. "A Pre-Registered Evaluation Protocol for Vulnerability-Host Prioritization:
   Calibration, Label Choice, and Operational Sensitivity."

Avoid "Calibrated ... Prioritization" as the lead noun phrase — it telegraphs "we
built a better model," inviting the incrementality critique before the abstract is
read.

## 2. Research problem
Paper 1 left a precise open question: under a capacity-constrained,
public-sector-shaped benchmark, **does calibrating the context-aware weights (and
choosing labels/operating conditions well) yield an operationally meaningful
improvement over EPSS/CVSS/KEV baselines — or not?** And: **how sensitive is any
such conclusion to label definition (A vs B), imputation, capacity ratio,
blackout/approver policy, and EPSS version?** Paper 1 used placeholder weights, a
single cell, and applied no statistics, so the question is genuinely unanswered.

## 3. Why this problem matters
- Practitioners/vendors routinely assert "context-aware/risk-based" scoring beats
  EPSS; that claim is rarely tested reproducibly with statistics and capacity
  constraints.
- A rigorous, pre-registered *negative or neutral* answer is itself valuable — it
  counters overclaiming in the RBVM space.
- Sensitivity/robustness reporting (label choice, imputation, capacity) is usually
  absent from prioritization papers; a reusable protocol fills a methodological gap.

## 4. Research gap
Learned/context-aware vulnerability prioritization exists (Deep VULMAN, VulnScore,
EPSS lineage) `[VERIFY]`. Scarce: **an open, reproducible, capacity-aware,
statistically-tested, label-robust, sensitivity-swept** comparison of calibrated
context-aware scoring vs EPSS/CVSS/KEV, with a frozen artifact and pre-registered
analysis. The gap is methodological rigor + reproducibility + honest sensitivity,
**not** "a new scoring model."

## 5. How it differs from Paper 1

| | Paper 1 | Paper 2 (this) |
|---|---|---|
| Type | Systems/benchmark paper | Analysis/results paper |
| Weights | placeholder (uncalibrated) | **calibrated** (logistic/ridge) + GBT comparator |
| Cells | single primary cell | **sensitivity grid** (capacity, blackout, approver, imputation, label, EPSS version) |
| Labels | Label A only | **Label A vs B robustness** |
| Statistics | none applied (descriptive) | **paired Wilcoxon + Holm + bootstrap CI + effect size + MDE** |
| Data | toy fixtures | **real public-feed snapshots** for vulns/exploits (synthetic fleet retained) — see §8 caveat |
| Claim | framework feasibility; neutral | **falsifiable comparative question**, answer reported either way |

## 6. How it reuses Paper 1 without duplicating it
Reuse, unchanged: feed clients + snapshot cache (no-future-leakage), synthetic
fleet generator, pair construction, feature frame, scheduler, audit log,
evaluation/statistics/reporting, controlled-run + freeze/verify. **Do not**
re-describe the framework in detail (cite Paper 1). **Do not** touch
`results/primary_full_v1/`; Paper 2 writes to a **new results namespace** (e.g.,
`results/paper2_*`) with its own freeze manifests. Duplication risk is mitigated by
making Paper 2 mostly *experiment configs + analysis + writing* with minimal new
code (calibration already implemented in Phase 6; GBT in Phase 7).

## 7. Proposed original contribution
Framed as **methodology + evidence**, not a model:
1. A **pre-registered evaluation protocol** (primary hypothesis, primary metric,
   primary cell fixed and hash-committed before running).
2. A **label-robustness analysis** (A vs B) quantifying dependence on the
   exploitation-label proxy.
3. A **sensitivity study** across operational axes (capacity, blackout, approver,
   imputation, EPSS version).
4. **Calibrated** context-aware scoring vs EPSS/CVSS/KEV with **paired statistics,
   effect sizes, and minimum detectable effect**, reported for all cells.
5. New **frozen, freeze-verified artifacts** per condition.
The contribution is the rigorous, reproducible *answer and protocol*, whatever the
sign of the result.

## 8. Candidate methods (assessed skeptically)
- **Calibrated logistic / ridge weights** (Phase 6, built). ⚠️ **Critical caveat:**
  calibration is meaningless on the 5-CVE toy fixtures. Paper 2 **must** use a
  realistic labeled set — real **public-feed snapshots** (NVD/EPSS historical back
  to 2021-04-14, KEV, PoC) on the synthetic fleet, with strict no-future-leakage and
  temporal train/gap/test. Biggest design requirement; also *reduces* Paper 1's
  "toy" limitation.
- **LightGBM comparator** (Phase 7; needs `libomp`). Stronger learned baseline.
- **Ablations** (`proposed_no_criticality`, `proposed_no_exposure`) — built; test
  whether host context adds value.
- **Label A vs B** — built; core robustness axis.
- **EPSS v3/v4 stratification** — include **only if** historical snapshots cleanly
  support version tagging; `[VERIFY]` availability/versioning, else drop.
- **Imputation / capacity / blackout / approver sensitivity** — framework-supported
  config sweeps.

## 9. Required experiment design
- **Pre-register** (write + hash-freeze) the analysis plan before running the
  primary experiment.
- Calibrate on **train** only; evaluate on **test**; never tune on test.
- 30 seeds (reuse controlled-run + checkpoint + freeze/verify); one frozen artifact
  per condition in a new namespace.
- Keep the sensitivity grid **small and pre-declared** (e.g., 3 capacity ratios ×
  {Label A,B} × {primary, light blackout} × {Policy A,B} × {median, zero
  imputation}); resist combinatorial explosion (drives p-hacking).
- Strict inspection + freeze on every artifact before analysis.

## 10. Required metrics (reuse Paper 1)
EHD / EEHDA (primary), relative_to_epss, fraction_of_oracle, precision/recall/nDCG@k,
KEV-deadline breach, capacity efficiency, scheduler feasibility, audit hash-chain
validity. All implemented; no new metric code expected.

## 11. Required statistical tests (reuse Phase 10)
Paired-by-seed comparison; **Wilcoxon signed-rank**; **Holm-Bonferroni** across the
strategy family / sensitivity cells (mandatory given multiplicity); **bootstrap/BCa
CIs**; **paired Cohen's d**; **minimum detectable effect** (report it — Paper 1
showed sub-0.5% spreads, so "significant" may still be operationally negligible).
Report effect sizes + CIs alongside every p-value.

## 12. Required citations / source categories
EPSS (Jacobs et al.), CVSS (FIRST), KEV/BOD 22-01 (CISA), Allodi & Massacci,
Sabottke et al.; learned prioritization (Deep VULMAN, VulnScore, VulRG);
calibration/regularized logistic + Platt scaling; LightGBM (Ke et al. 2017);
Wilcoxon 1945 / Holm 1979 / Efron 1987; learning-to-rank + pre-registration/
reproducibility methodology. All `[VERIFY]`; reuse Paper 1's confirmed Tier-1 set;
**no fabrication**.

## 13. Risks of overclaiming
- If calibrated beats EPSS on synthetic data → claim only "**under this synthetic
  benchmark**," never real-world/government superiority.
- If it does not → report plainly (as Paper 1 did). Do not bury it.
- Avoid "calibration solves prioritization"; at most "calibration narrows/closes/
  does-not-close the gap under these conditions."

## 14. Risks of p-hacking / benchmark overfitting (highest severity)
- **Multiplicity:** many cells × strategies → false positives. *Mitigation:*
  pre-register; Holm-Bonferroni; report the full grid, not the best cell.
- **Grading own homework / benchmark overfitting:** evaluating on the same synthetic
  benchmark the authors built. *Mitigation:* real public-feed labels, temporal
  hold-out, open artifact for external replication, explicit limitation. **Cannot
  be fully eliminated** with synthetic-only evaluation — state it.
- **Test-split leakage during calibration:** *Mitigation:* calibrate on train only;
  no-future-leakage + gap split already enforced.
- **Effect-size inflation:** declaring significance on negligible effects.
  *Mitigation:* report MDE + CIs + practical-significance threshold.
- **Config fishing:** trying conditions until one wins. *Mitigation:* pre-registered
  plan + freeze/verify; the freeze hash predates results.

## 15. Confidentiality risks
**Near zero.** Synthetic fleet + public feeds only; no compliance artifacts, no
employer data. Keep Paper 1's data warning.

## 16. Publishability score: **6.5 / 10**
- Reframed (pre-registered robustness/sensitivity protocol + honest result):
  **6.5/10** at reproducibility/empirical-security venues (DTRAP, EuroS&P/workshop,
  Computers & Security). A clean, pre-registered *negative* result is publishable.
- Naive ("we calibrated weights and they're better"): **4/10** — incremental +
  overfitting critique.
- Ceiling limited by synthetic-only evaluation, own-benchmark, and the strong
  possibility of a neutral result.

## 17. EB1A evidence strength: **5.5 / 10**
- Two coherent papers (benchmark + rigorous results/robustness) > one;
  pre-registration + applied statistics show methodological maturity; reduces
  Paper 1's "toy/placeholder" weakness.
- Capped by self-published status (no peer review/citations yet) and synthetic
  scope. A *positive* statistically-sound result would help more but **must not be
  engineered**.

## 18. Go / No-Go decision: **CONDITIONAL GO**
Proceed only if all three hold:
1. **Pre-registration first** — write and hash-freeze the analysis plan before the
   primary experiment.
2. **Sufficient calibration data** — move from toy fixtures to real public-feed
   snapshots (resolve EPSS-version `[VERIFY]` and data-window feasibility) so
   calibration is meaningful; otherwise the calibration claim is empty → NO-GO.
3. **Robustness-methodology framing** — contribution is the protocol + honest
   answer, not a superiority claim; accept that a neutral result is the likely and
   publishable outcome.

If (2) cannot be satisfied with lawfully usable data, **PIVOT** to a pure
label-robustness/sensitivity study using a *richer synthetic* exploitation-label
model (still useful, lower ceiling). Not an outright NO-GO — but it **is
incremental**; if the priority is maximal EB1A novelty, a more distinct topic may
serve better than a Paper-1 companion.

**Why stronger than the killed compliance Paper 2:** (a) low prior-art collision
(differentiates from generic learned prioritization via reproducibility +
capacity-awareness + pre-registered statistics; the compliance paper collided
head-on with April-2026 OSCAL evidence work); (b) near-zero confidentiality risk
(vs high); (c) reuses a built, tested, frozen artifact (faster, lower-risk);
(d) crisp falsifiable question; framework already computes every needed metric/stat.

## 19. Final recommended outline (if CONDITIONAL GO satisfied)
1. Introduction (the open question from Paper 1; pre-registered) · 2. Background
(CVSS/EPSS/KEV; calibration; capacity-constrained remediation) · 3. Related Work
(learned prioritization; differentiate via reproducibility/robustness) ·
4. Problem & Pre-Registered Hypotheses (primary + secondary; non-goals) ·
5. Benchmark Recap (cite Paper 1; reused vs new) · 6. Data & Labels (public-feed
snapshots; Label A vs B; no-future-leakage) · 7. Calibration Methods (logistic/
ridge; GBT comparator; train-only) · 8. Experiment Design & Sensitivity Grid
(pre-declared) · 9. Metrics & Statistical Protocol (Wilcoxon/Holm/bootstrap/effect
size/MDE) · 10. Results (primary cell; sensitivity; label robustness — report all) ·
11. Discussion · 12. Threats to Validity (own-benchmark, synthetic, multiplicity) ·
13. Limitations · 14. Future Work · 15. Conclusion · Abstract.

---

**Bottom line:** CONDITIONAL GO — the right low-risk, integrity-forward next paper
and a clean companion to Paper 1, but moderate-novelty and likely neutral-result;
publishability hinges on pre-registration, meaningful calibration data, and
robustness-methodology framing — not on beating EPSS.

**Next step options:** (a) proceed to Paper 2 Step 2 (prior-art falsification for
this topic) and draft the pre-registration plan; or (b) weigh a more distinct
Paper 2/3 topic first. No drafting has occurred.
