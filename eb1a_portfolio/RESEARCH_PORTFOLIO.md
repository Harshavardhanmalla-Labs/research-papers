# Research Portfolio — Harshavardhan Malla
## Evidence of Original Contributions in Cybersecurity Research
### EB-1A Petition Exhibit — Research Dossier

**Prepared:** 2026-05-31 (original 4-paper version) · Updated 2026-06-05 (8-paper consolidated program)
**Field of Extraordinary Ability:** Cybersecurity — Vulnerability Management, Anomaly Detection, and Reproducible Security Research

---

## Overview

This dossier documents **eight original research papers** in cybersecurity that collectively demonstrate sustained, independent, publication-ready scholarly contribution in a specialized field. Each paper addresses an open problem in security operations, employs rigorous pre-registered methodology, and is prepared for submission to peer-reviewed venues. **All research is conducted entirely with synthetic, seeded data — no production, employer, or government operational data was used at any stage.**

The eight papers form a coherent multi-year research program. Their cumulative output is **approximately 55,000 frozen Precision@K evaluation rows** across the synthetic EEHDA fleet, with **approximately 35 pre-registered hypotheses** locked-and-evaluated honestly. Several pre-registered hypotheses were rejected by the data; those rejections are reported as findings rather than smoothed over, in keeping with the open-science discipline this program is designed to demonstrate.

### The eight papers

1. **Paper 1 (VulnPrio)** — Single-window context-aware vulnerability prioritization on a synthetic government endpoint fleet. **Negative result honestly reported:** thirteen scoring strategies are statistically indistinguishable on Expected Exploited Host-Days; infrastructure (reproducible benchmark + tamper-evident audit log) is the contribution.

2. **Paper 2 (CalibScore)** — Can real public-feed data calibrate the Paper 1 benchmark weights? Pre-registered with eight stop rules; the answer is a documented negative feasibility finding.

3. **Paper 3 (HygieneBench)** — First open synthetic benchmark for cyber-hygiene anomaly detection covering identity, endpoint, and patch telemetry. 810-run evaluation across eight detection methods and seven tasks; honest finding that **simple rule baselines beat ML on 86.2% of configurations**, with two exceptions (group-membership drift and patch hygiene) where ML adds discriminative signal.

4. **Paper 4 (HygienePrio)** — A scoring framework integrating Hygiene Risk Score (patch posture, AD exposure, telemetry freshness) with EPSS. Pre-registered evaluation; **+31 percentage-point Precision@50 over EPSS-only** at a single window on 25/25 evaluation seeds. Closes the loop opened by Paper 1's null result.

5. **Paper 5 (Temporal Stability)** — Does the Paper 4 advantage persist across rolling maintenance windows? Six-window simulation on 25 evaluation seeds; HygienePrio-full outperforms EPSS-only in **150 of 150 window-seed pairs**, while EPSS-only decays from P@50=0.331 at W1 to 0.034 at W6 (89.7% drop). Pre-registered H3 (fixed-weight sufficiency) rejected — per-window recalibration adds up to +21.3 pp.

6. **Paper 6 (Capacity-Indexed Decay)** — Two-dimensional sweep over remediation capacity K ∈ {10,...,200} and CVE arrival rate λ ∈ {1,...,12}. Pre-registered with four hypotheses; **all four rejected**, including the headline H4 that HygienePrio retains its absolute floor — at K = 200/λ = 1 the W6 mean falls to 0.062. The per-pair advantage of HygienePrio over EPSS-only persists at 96.0% across the grid; the absolute floor does not.

7. **Paper 7 (Online Recalibration — Consolidated)** — A pre-registered comparison of six deployable recalibration procedures: **E1 lag-1 online**, **E2 multi-window smoothing**, **E3 single-τ adaptive change-point**, **E4 τ sensitivity sweep**, **E5 capacity-aware τ vector**, **E6 one-sided CUSUM**. Each experiment's protocol was locked before its evaluation seeds were inspected; the chain of pre-registered rejections drives the experimental design. Cumulative finding: the deployable recipe is **capacity-conditional** — lag-1 below K = 100, CUSUM(0.04, 0.10) at K = 200 (the only operationally meaningful gain over the static gate in the entire program: +0.9 pp).

8. **Paper 8 (Self-Trajectory Evaluation)** — An evaluation-methodology contribution. Re-runs every method on its own fleet trajectory (rather than the shared HygienePrio-full-driven trajectory used in Papers 5–7), and shows that **Paper 6's headline K = 200 collapse is substantially selection-induced rather than intrinsic**. Under EPSS-driven, HRS-driven, and Random-driven trajectories at K = 200, HygienePrio reaches Precision@50 of 0.701–0.713 — approximately 10× higher than on its self-driven trajectory.

Together these papers demonstrate: (a) original formulation of open research problems, (b) careful experimental design with pre-registration and reproducibility, (c) intellectual honesty through honest null-result and negative-result reporting (approximately 15 pre-registered hypothesis rejections across the program, each reported as observed rather than smoothed), and (d) infrastructure contributions (benchmark suites, datasets, evaluation harnesses, open scorers, simulators) that enable the broader research community to reproduce and extend the work.

---

## Paper 1: VulnPrio — Evidence-Based Vulnerability Prioritization

### Full Title
Context-Aware Vulnerability Prioritization for Government Endpoint Fleets: Integrating Exploit Intelligence, Asset Criticality, and Endpoint Telemetry

### Submission Target
IEEE workshop on security measurement and practice (e.g., USENIX Security workshop, IEEE S&P workshop, or ACM CCS workshop on quantitative security)

### Status
Drafting — submission-ready LaTeX at `paper1-vuln-prioritization/paper/submission/ieee/`

### Technical Summary

VulnPrio introduces a seven-feature linear composite scoring framework embedded in a five-phase, capacity-constrained scheduler with KEV-deadline overrides and append-only SHA-256 hash-chained audit logs. The score combines EPSS exploit probability, KEV membership, CVSS base score, asset criticality, network exposure, urgency, and remediation complexity.

**Key evaluation results:**
- 30 independent random seeds × 13 strategies = 390 scheduled runs
- Primary metric: Expected Exploited Host-Days (EHD) ≈ 1.12 × 10⁶ host-days
- **Central finding (honest null):** All 13 strategies are statistically indistinguishable on EHD (Wilcoxon signed-rank + Holm correction, all 78 pairwise adjusted p > 0.05; inter-strategy spread < 0.5% of mean)
- **Audit integrity:** 100% of 390 hash-chained audit logs verify without error
- **Infrastructure contribution:** Fully reproducible, open benchmark for future prioritization research

### Significance Statement

The scientific community often suffers from publication bias toward positive findings. VulnPrio demonstrates that rigorous negative-result reporting — a statistically established null finding with full apparatus — is a meaningful contribution. The infrastructure (reproducible benchmark + tamper-evident audit logs) enables any future prioritization system to be evaluated under identical conditions. The audit logging mechanism addresses an emerging regulatory requirement for automated security decision records in government environments.

---

## Paper 2: CalibScore — Public-Feed Calibration Feasibility

### Full Title
Can Public Vulnerability Feeds Calibrate a Synthetic Prioritization Benchmark? A Pre-Registered Feasibility Study

### Submission Target
IEEE CSET — Cyber-Security Experimentation and Test (USENIX workshop on Cyber-Security Experimentation and Test)

### Status
Drafting — submission-ready LaTeX at `paper1-vuln-prioritization/paper2/submission/cset/`

### Technical Summary

A pre-registered feasibility study, locked with eight stop rules before any data was inspected, asking whether public CVE / EPSS / KEV feeds can be used to calibrate the Paper 1 benchmark weights. The protocol enumerates the conditions under which a calibration attempt would be declared successful, partially successful, or infeasible.

**Outcome:** Documented negative feasibility finding. The pre-registration's stop rules surfaced the infeasibility cleanly rather than letting it be retrofitted into a positive narrative. This is a methodological contribution as much as a substantive one — it demonstrates that pre-registration discipline can surface negative results that would otherwise be hidden by selective reporting.

---

## Paper 3: HygieneBench — Cyber-Hygiene Anomaly Detection Benchmark

### Full Title
A Reproducible Synthetic Benchmark for Cyber-Hygiene Anomaly Detection Across Identity, Endpoint, and Patch Telemetry

### Submission Target
ACM CCS AISec Workshop (Annual workshop on AI security; 6–8 page workshop submission)

### Status
Submission-ready: 7 pages, compiles cleanly via `tectonic`. Camera-ready item: Zenodo DOI for the artifact deposit (placeholder noted in conclusion).

### Technical Summary

HygieneBench is the first open synthetic benchmark covering identity (Active Directory) state, endpoint patch posture, and telemetry freshness in a single jointly-evolving fleet model. It defines seven anomaly-detection tasks (T1–T7) and twelve anomaly classes (AH-01 through AH-12), evaluated by an eight-method panel that combines rule baselines with unsupervised ML (Isolation Forest, LOF, OCSVM, Linear AE, temporal z-score, graph isolation forest).

**Key empirical findings (810-run evaluation):**
- **86.2% negative-result rate** — ML fails to consistently beat rule baselines by Δ ≥ 0.05 across 608/705 configurations
- **ML adds value on T2 (group-membership drift):** temporal z-score AP = 0.951 vs rule 0.766 (Δ = +0.185, C-BASE condition)
- **ML adds value on T5 (patch/vulnerability hygiene):** OCSVM AP = 0.668 vs rule 0.458 (Δ = +0.210)
- **Telemetry staleness (C-STALE)** consistently degrades detection by Δ ≈ −0.17 AP across tasks
- **15 frozen condition × seed datasets** (n = 1000 users, 11 tables, 110 anomaly labels per dataset)

### Significance Statement

The benchmark addresses a gap in the open-research literature: no prior open synthetic dataset covers identity, endpoint, and patch telemetry jointly under a controlled anomaly-injection model. The honest 86.2% null-result reporting demonstrates that rule baselines remain competitive for cyber-hygiene anomalies and that ML claims in this domain require careful baseline comparison.

---

## Paper 4: HygienePrio — Hygiene-Augmented EPSS Prioritization

### Full Title
HygienePrio: Cyber-Hygiene Signal Augmentation for EPSS-Weighted Vulnerability Prioritization

### Submission Target
IEEE Transactions on Network and Service Management (TNSM)

### Status
Submission-ready: 14 pages, compiles cleanly. Camera-ready item: self-citation DOI for the Paper 1 reference.

### Technical Summary

HygienePrio integrates a three-dimensional Hygiene Risk Score (HRS) — combining patch posture (0.50), AD exposure (0.30), and telemetry freshness (0.20) — with the EPSS exploit-likelihood signal in a calibrated four-term scorer:

```
S(h, c) = 0.7·EPSS(c) + 0.5·HRS(h) + 0.1·KEV_recency(c) + 0.2·(EPSS(c) · HRS(h))
```

Weights are pre-calibrated by grid search on five held-out fleet seeds; evaluation is on a separate 25-seed set. The simulator and scorer are released under MIT licence.

**Key results:**
- HygienePrio-full mean Precision@50 = 0.509 vs EPSS-only's 0.202 (≈ **31 percentage-point improvement**)
- **Improvement on 25 of 25 evaluation seeds**, non-overlapping percentile bootstrap CIs
- **Patch posture is the dominant hygiene dimension:** ≈ 20 pp Precision@50 drop when patch posture is removed
- AD exposure: ≈ 9 pp drop; telemetry freshness: ≈ 2 pp drop (CIs overlap)

### Significance Statement

HygienePrio operationalises the Paper 3 finding (hygiene signals carry discriminative structure) in a deployable scorer and resolves the Paper 1 null result by identifying the missing signal (host-level hygiene posture, not additional CVE-level features). The +31 pp improvement is the largest cleanly-reported margin on this fleet model in the open literature; the patch-posture-dominance finding gives operations teams a concrete instrumentation priority.

---

## Paper 5: Temporal Stability of Hygiene-Augmented Prioritization

### Full Title
Temporal Stability of Hygiene-Augmented Vulnerability Prioritization Across Rolling Maintenance Windows

### Submission Target
IEEE TNSM (journal mode, IEEEtran)

### Status
Submission-ready: 8 pages, compiles cleanly. Camera-ready item: Paper 4 self-citation DOI.

### Technical Summary

The first multi-window evaluation of vulnerability prioritization on the EEHDA fleet. The Paper 4 scorer is held fixed at its calibrated weights and applied across six consecutive bi-weekly maintenance windows on 25 evaluation seeds. The simulator extends Paper 4's generator with explicit fleet-state evolution (patch application reduces patch debt; Poisson(3) new-CVE arrivals; EPSS random walk; telemetry staleness drift).

**Key results (frozen 750-row CSV):**
- **HygienePrio-full outperforms EPSS-only in 150 of 150 window-seed pairs**
- EPSS-only decays from mean P@50 = 0.331 at W1 to 0.034 at W6 (**89.7% relative drop**)
- HygienePrio-full maintains mean P@50 ≥ 0.499 at every window
- HRS-only baseline overtakes EPSS-only at W2 and dominates EPSS-only at every subsequent window
- Absolute HygienePrio-vs-EPSS gap grows from 26.4 pp (W1) to 46.5 pp (W6)
- **H3 rejected:** per-window recalibration adds up to +21.3 pp over fixed weights — fixed-weight sufficiency falsified

### Significance Statement

This paper retroactively reframes Paper 1's null result: that null was measured in the regime where EPSS-only is at maximum strength. Across six windows of remediation, EPSS-only decays toward random ranking while hygiene-augmented scoring sustains discriminative power. The operational implication is concrete: organisations relying solely on EPSS should expect degrading returns after roughly four to six weeks of active patching.

---

## Paper 6: Capacity-Indexed Decay

### Full Title
Capacity-Indexed Decay of Exploit-Likelihood Vulnerability Prioritization

### Submission Target
IEEE TNSM

### Status
Submission-ready: 8 pages, compiles cleanly.

### Technical Summary

A pre-registered two-dimensional sweep over remediation capacity K ∈ {10, 25, 50, 100, 200} and Poisson CVE arrival rate λ ∈ {1, 3, 6, 12}. Twenty (K, λ) cells × 25 evaluation seeds × 6 windows × 5 methods = **15,000 frozen result rows**. The sweep characterises how the prioritization landscape depends on operating regime.

**Pre-registered hypotheses (H1–H4) all rejected, in scientifically interesting ways:**

- **H1, H2 (monotonicity predictions):** rejected — the underlying (K, λ) dynamics are not cleanly monotone in either capacity or arrival rate.
- **H3 (steady-state ratio):** rejected — no cell in the studied grid produces a steady-state EPSS regime; decay is strictly negative everywhere.
- **H4 (HygienePrio retention):** **rejected, with concrete operational consequence** — at K = 200, HygienePrio-full's W6 cell mean collapses to 0.062 (at λ = 1) through 0.116 (at λ = 12). High-capacity remediation exhausts the high-HRS tail of the fleet, leaving the residual backlog with no discriminative structure.

**The robustness claim that survives:** HygienePrio-full beats EPSS-only at P@50 in **2,881 of 3,000 (96.0%)** of (cell, seed, window) triples. The per-pair advantage is regime-robust; the absolute floor is not.

### Significance Statement

The paper documents that headline performance numbers from single-cell evaluations can mislead. The honest H4 rejection — including the specific cell (K = 200, λ = 1) where HygienePrio collapses to 0.062 — would be hidden by any procedure that did not lock H4 in advance. The framing teaches the field that ``HygienePrio retains ~0.5 P@50'' is a single-cell statement, not a method-level claim.

---

## Paper 7: Online Recalibration for HygienePrio (Consolidated)

### Full Title
Online Recalibration for Hygiene-Augmented Vulnerability Prioritization: A Pre-Registered Comparison of Six Procedures

### Submission Target
IEEE TNSM (journal article, 9 pages)

### Status
Submission-ready: 9 pages, compiles cleanly. This is a **consolidated journal article** covering six experiments (E1–E6) under a single pre-registration umbrella, with 27 hypotheses locked-and-evaluated across the program.

### Technical Summary

Paper 5 introduced an offline-peek recalibration ablation that lifts P@50 by up to +21.3 pp at W2 — but the peek procedure is not deployable. Paper 6 documented that the same regime that produces the +21.3 pp ceiling also exhibits capacity-dependent absolute collapse at K ≥ 100. The present paper asks: can any deployable recalibration procedure recover the offline ceiling at moderate capacity AND avoid the absolute collapse at high capacity?

Six experiments, each pre-registered and locked before its evaluation-seed P@50 was inspected:

- **E1 Lag-1 online (1,350 rows).** Refit weights on calibration seeds at window w − 1. **Recovers offline ceiling at K ≤ 100 (ρ ≈ 1.0); harms performance at K = 200 (ρ = −0.66).**
- **E2 Multi-window smoothing (2,250 rows).** EWMA-3 and trailing-mean-3 over calibration history. **All four hypotheses rejected: smoothing AMPLIFIES the K = 200 hazard (EWMA ρ = −0.94) rather than reversing it.** Falsifies the naive "more history reduces variance" prior.
- **E3 Single-τ adaptive change-point (2,250 rows).** Magnitude detector at τ = 0.05 reverting to fixed weights on fire. **First procedure in the program to avoid the K = 200 hazard (H1 supported, +0.7 pp over fixed cell-mean).** Pays a K = 50 over-firing cost (H2 rejected, −5.3 pp).
- **E4 τ sensitivity sweep (11,250 rows).** Sweep over τ ∈ {0.02, …, 0.10}. **Central negative result: no τ in the grid satisfies both pre-registered tolerances; the simple magnitude detector cannot reach the joint feasibility region.** H2/H4 sign-direction protocol errors also surfaced honestly.
- **E5 Capacity-aware τ vector (2,700 rows).** Pre-registered τ_K = {50: 0.20, 100: 0.05, 200: 0.02}. **First procedure to reach the joint feasibility region — but its K = 200 cell mean equals the static gate's cell mean exactly (0.2664 to four decimals).** Validates the gate without improving on it.
- **E6 One-sided CUSUM (2,700 rows).** Pre-registered k = 0.04, h = 0.10 on the calibration-target shift. **First detector to beat the static gate at K = 200 by +0.9 pp** — the only operationally meaningful gain over the static gate in the entire program. H2 binary test rejects by 0.001 pp; substantive direction supported. K = 50 over-firing (H1 rejected, −3.9 pp) identifies per-K (k_K, h_K) as the natural next research target.

### The deployable recipe (capacity-conditional)

- **K ≤ 100:** deploy lag-1 online recalibration directly (E1, ρ ≈ 1.0).
- **K = 200:** deploy CUSUM(0.04, 0.10) (E6, +0.9 pp over the static gate).
- **Mixed K:** per-K CUSUM (k_K, h_K) vector required (future work).

### Significance Statement

Twenty-seven pre-registered hypotheses, six experiments, ~22,500 frozen P@50 rows, and a chain of honest rejections that constrains the solution space cleanly. The cumulative finding is methodological as much as substantive: the deployable-calibration question has a capacity-conditional answer, and reaching it required falsifying the smoothing prior, sweeping the τ axis to negative-feasibility, gating the magnitude detector by capacity, and finally introducing CUSUM evidence accumulation. Each step is locked before evaluation and reported honestly.

---

## Paper 8: Self-Trajectory Evaluation

### Full Title
Self-Trajectory Evaluation of Hygiene-Augmented Vulnerability Prioritization

### Submission Target
IEEE TNSM

### Status
Submission-ready: 8 pages, compiles cleanly.

### Technical Summary

A methodological contribution that addresses the selection-policy coupling threat that all of Papers 5–7 inherit. In those papers, HygienePrio-full under fixed weights drives the fleet trajectory for every method scored at every window; the trajectory is shared. This evaluation convention is necessary for cross-method comparison but introduces an unmeasured bias: each method is scored against a backlog its own weights did not produce.

Paper 8 re-runs each method on its OWN trajectory (each method drives the fleet using its own top-K selection) and quantifies the resulting cross-trajectory differences. **All three pre-registered hypotheses are rejected.**

**Key results (frozen 7,500-row CSV):**
- At K = 200, HygienePrio on its **own** trajectory falls to P@50 = 0.075 (the Paper 6 collapse pattern).
- Under EPSS-driven trajectory at K = 200, **HygienePrio reaches P@50 = 0.701** — approximately **10× higher**.
- Under HRS-driven trajectory: 0.713. Under Random-driven trajectory: 0.706.
- **Paper 6's headline K = 200 collapse is substantially selection-induced, not intrinsic to HygienePrio's scoring weights.**

### Significance Statement

This is a paper about evaluation methodology, not about a calibration recipe. It quantifies an unmeasured bias in the standard multi-window prioritization-evaluation framework used in Papers 5–7 (and, to our knowledge, in the broader literature). The result re-attributes a headline collapse to a methodological artifact, sharpening every subsequent claim in the program. Both Papers 6 and 7 cite Paper 8 as the answer to "but isn't your fixed-trajectory comparison biased?" — yes, and Paper 8 measures by how much.

---

## Cross-Paper Synthesis

**A coherent multi-year research program:** The eight papers form a sequence in which each paper's contribution is either a foundation for the next (Papers 3 → 4 → 5 → 6) or an honest methodological refinement of the previous result (Papers 7 and 8). The pre-registered rejection patterns across the program are themselves a substantive contribution — they map the boundary between what the synthetic-fleet evaluation framework can and cannot conclude.

| Paper builds on | Foundation laid for |
|---|---|
| Paper 1 (VulnPrio null) | Paper 4 (HygienePrio: identifies the missing signal) |
| Paper 3 (hygiene benchmark) | Paper 4 (hygiene dimension design + HRS components) |
| Paper 4 (HygienePrio single-window) | Paper 5 (does the advantage persist temporally?) |
| Paper 5 (temporal stability) | Paper 6 (how does it scale across (K, λ)?) |
| Paper 6 (K=200 collapse) | Paper 7 (can deployable recalibration recover it?) |
| Paper 7 (calibration recipe) | Paper 8 (is the collapse intrinsic or selection-induced?) |
| Paper 8 (selection coupling) | Future closed-loop calibration work |

**Common methodological thread.** All eight papers share:
- Pre-registered analysis plans before examining results (approximately 35 hypotheses locked across the program)
- Honest null/negative-result reporting as a first-class contribution (approximately 15 rejected hypotheses reported as observed)
- Fully synthetic seeded data (no production or employer data)
- Open reproducibility artifacts (generator, code, frozen results)
- Multiple-seed evaluation with percentile bootstrap CIs (10,000 resamples)
- Stop rules in each protocol that govern abstract-rewriting if a hypothesis is rejected

**Cumulative frozen evidence:** approximately 55,000 Precision@K rows across the eight papers, all reproducible from per-paper seed lists.

---

## Compilation Instructions (for Attorneys/Petitioners)

All papers compile with [Tectonic](https://tectonic-typesetting.github.io/) (recommended) or pdfLaTeX + BibTeX:

```bash
# Using Tectonic (recommended)
tectonic "paper1-vuln-prioritization/paper/submission/ieee/main.tex"
tectonic "paper1-vuln-prioritization/paper2/submission/cset/main.tex"
tectonic "paper3/submission/acm/main.tex"
tectonic "paper4/submission/ieee/main.tex"
tectonic "paper5/submission/ieee/main.tex"
tectonic "paper6/submission/ieee/main.tex"
tectonic "paper7/submission/ieee/main.tex"
tectonic "paper8/submission/ieee/main.tex"
tectonic "eb1a_portfolio/exhibit_cover.tex"

# Merge all into portfolio PDF
python3 eb1a_portfolio/merge_portfolio.py
# → Output: eb1a_portfolio/EB1A_Research_Portfolio_Malla_2026.pdf
```

Requires: Tectonic (`brew install tectonic` on macOS) or MacTeX (macOS) or MiKTeX (Windows).

---

## Evidence Index for EB-1A Petition

| Exhibit | Type | Paper | Pages |
|---|---|---|---|
| Exhibit A | Research paper | Paper 1 (VulnPrio) | 8 |
| Exhibit B | Research paper | Paper 2 (CalibScore) | 8 |
| Exhibit C | Research paper | Paper 3 (HygieneBench, ACM AISec) | 7 |
| Exhibit D | Research paper | Paper 4 (HygienePrio, IEEE TNSM) | 14 |
| Exhibit E | Research paper | Paper 5 (Temporal Stability, IEEE TNSM) | 8 |
| Exhibit F | Research paper | Paper 6 (Capacity-Indexed Decay, IEEE TNSM) | 8 |
| Exhibit G | Research paper | Paper 7 (Online Recalibration consolidated, IEEE TNSM) | 9 |
| Exhibit H | Research paper | Paper 8 (Self-Trajectory Evaluation, IEEE TNSM) | 8 |
| Pre-reg ledger | Pre-registration | ~35 locked hypotheses across the program, archived in each paper's `design/` directory |
| Frozen data | Benchmark data | ~55,000 Precision@K rows across all eight papers' `results/` directories |
| Code | Code artifacts | Synthetic EEHDA generator + per-paper analysis scripts under MIT licence |

**Total submission pages: 70** (8 papers averaging ~9 pages each).

---

## Field-Impact Statement

This program contributes to four overlapping fields:

1. **Cyber-hygiene anomaly detection (Paper 3):** the first open synthetic benchmark covering identity, endpoint, and patch telemetry jointly. The honest 86.2% null-result reporting is itself a contribution to a literature that suffers from ML-positivity bias.

2. **Vulnerability prioritization (Papers 1, 4, 5, 6, 7):** the first pre-registered multi-window evaluation of a hygiene-augmented prioritization scorer, with the deployable calibration recipe (Paper 7) and the capacity-conditional regime characterisation (Paper 6).

3. **Evaluation methodology in security research (Paper 8):** the first quantification of selection-policy coupling bias in multi-window prioritization evaluation; the result re-attributes a headline collapse to a methodological artifact and changes how subsequent comparisons should be designed.

4. **Reproducible security research practice:** the discipline of pre-registration with locked decision rules and stop rules, applied across approximately 35 hypotheses, ~15 of which were rejected and reported honestly. This program is intended as a worked example of how pre-registration sharpens claims in security research, parallel to its established role in clinical and behavioural sciences.

---

*This portfolio was self-assembled by the researcher. All claims in this document are documented with traceable artifacts in the research directories. No employer data, government operational data, or production system data was used in any paper.*
