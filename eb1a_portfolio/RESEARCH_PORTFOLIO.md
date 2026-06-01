# Research Portfolio — Harshavardhan Malla
## Evidence of Original Contributions in Cybersecurity Research
### EB-1A Petition Exhibit — Research Dossier

**Prepared:** 2026-05-31  
**Field of Extraordinary Ability:** Cybersecurity — Vulnerability Management, Anomaly Detection, and Reproducible Security Research

---

## Overview

This dossier documents four original research papers in cybersecurity that collectively demonstrate sustained, independent, publication-ready scholarly contribution in a specialized field. Each paper addresses an open problem in security operations, employs rigorous reproducible methodology, and is prepared for submission to peer-reviewed venues. All research is conducted entirely with synthetic, seeded data — no production, employer, or government operational data was used at any stage.

The four papers form a coherent research program:

1. **Paper 1 (VulnPrio)** establishes a benchmark infrastructure for context-aware vulnerability prioritization with a fully reproducible, audit-evidence-producing evaluation.
2. **Paper 2 (CalibScore)** asks whether real public-feed data can calibrate the Paper 1 benchmark weights — and rigorously documents a negative feasibility finding with pre-registered methodology.
3. **Paper 3 (HygieneBench)** introduces a novel open benchmark for cyber-hygiene anomaly detection, jointly covering identity state, endpoint patch posture, and telemetry freshness — a domain with no prior public benchmark.
4. **Paper 4 (HygienePrio)** closes the loop opened by Paper 1's null result: it demonstrates that host-level hygiene posture (patch debt, AD exposure, telemetry freshness) is the missing signal for meaningful EPSS-weighted prioritization improvement.

Together these papers demonstrate: (a) original formulation of open research problems; (b) careful experimental design with pre-registration and reproducibility; (c) intellectual honesty through honest null-result and negative-result reporting; and (d) infrastructure contributions (benchmark suites, datasets, evaluation harnesses, open scorers) that enable the broader research community to reproduce and extend the work.

---

## Paper 1: VulnPrio — Evidence-Based Vulnerability Prioritization

### Full Title
Context-Aware Vulnerability Prioritization for Government Endpoint Fleets: Integrating Exploit Intelligence, Asset Criticality, and Endpoint Telemetry

### Submission Target
IEEE workshop on security measurement and practice (e.g., USENIX Security workshop, IEEE S&P workshop, or ACM CCS workshop on quantitative security)

### Status
Drafting — submission-ready LaTeX at `paper1-vuln-prioritization/paper/submission/ieee/`

### Technical Summary

Vulnerability remediation in large endpoint fleets is constrained by finite patch capacity, regulatory deadlines (CISA BOD 22-01), and the continuous influx of newly published CVEs. The standard heuristic — rank by CVSS severity — explicitly does not account for exploit likelihood, asset criticality, network exposure, or operational complexity. This paper introduces **VulnPrio**, a seven-feature linear composite scoring framework:

```
score(h,v) = w_E·E + w_K·K + w_S·S + w_C·C + w_X·X + w_U·U − w_R·R
```

Where E = EPSS exploit probability, K = KEV membership, S = CVSS base score, C = asset criticality, X = network exposure, U = urgency, R = remediation complexity. The score is embedded in a five-phase, capacity-constrained scheduler with KEV-deadline overrides and append-only SHA-256 hash-chained audit logs — a tamper-evident decision record mechanism designed for regulatory compliance environments.

**Key evaluation results:**
- 30 independent random seeds × 13 strategies = 390 scheduled runs
- Primary metric: Expected Exploited Host-Days (EHD) ≈ 1.12 × 10⁶ host-days
- **Central finding (honest null):** All 13 strategies are statistically indistinguishable on EHD (Wilcoxon signed-rank + Holm correction, all 78 pairwise adjusted p > 0.05; inter-strategy spread < 0.5% of mean)
- **Audit integrity:** 100% of 390 hash-chained audit logs verify without error
- **Infrastructure contribution:** Fully reproducible, open benchmark for future prioritization research

### Significance Statement

The scientific community often suffers from publication bias toward positive findings. VulnPrio demonstrates that rigorous negative-result reporting — a statistically established null finding with full apparatus — is a meaningful contribution. The infrastructure (reproducible benchmark + tamper-evident audit logs) enables any future prioritization system to be evaluated under identical conditions. The audit logging mechanism addresses an emerging regulatory requirement for automated security decision records in government environments.

**What makes this extraordinary:** Most vulnerability prioritization papers claim superiority; this one rigorously proves indistinguishability and reports it honestly. The benchmark infrastructure is the contribution, not the performance number.

---

## Paper 2: CalibScore — When Calibration Fails

### Full Title
When Calibration Fails: A Failure-Aware Public-Feed Gate for Vulnerability Prioritization Under Sparse Exploit Labels

### Submission Target
USENIX CSET (primary); LASER Workshop (backup 1); ACM DTRAP (backup 2)

### Status
Drafting — submission-ready LaTeX at `paper1-vuln-prioritization/paper2/submission/cset/`

### Technical Summary

Paper 1's scoring framework uses placeholder weights. The natural follow-on question: can we calibrate those weights from real public-feed data (EPSS v3, CISA KEV, NVD)? This paper answers: **not yet, for a realistic public-sector fleet.**

The paper contributes a **pre-registered, failure-aware gate methodology** for deciding whether calibration is feasible before it is attempted:

1. **Chunked acquisition:** NVD + EPSS APIs queried in ≤120-day chunks with rate limiting, paging, and resumable checkpointing
2. **Multi-t₀ aggregation:** 18 monthly reference dates spanning the EPSS v3 era (2023-03-07 to 2025-03-16), counting unique positive CVEs across all windows
3. **Three-tier gate decision:** GO (≥50 unique positives), CAUTION (20-49), PIVOT (<20)
4. **Pre-registered stop-rule registry:** 8 stop rules committed before any API query was executed

**Key result:**
- 2,688 catalog-matched CVEs from a 31-product public-sector fleet
- Only **7 unique positive CVEs** across 18 monthly windows (positive rate ≈ 0.26%)
- Gate decision: **PIVOT** — calibration not attempted
- Descriptive sensitivity sweep: 6 fixed design-prior weight vectors across capacity, blackout, and feature-ablation axes; BCa CIs are so wide ([0.00, 0.71] for Top-10 coverage) that no vector can be distinguished from any other, confirming the gate decision

### Significance Statement

This paper introduces a research methodology concept — the **failure-aware gate** — that any practitioner can apply before attempting public-feed weight calibration. The finding that 7 of 2,688 fleet-matched CVEs have confirmed exploitation labels over 24 months is a concrete, reproducible data-density boundary. The paper provides a scaling formula for practitioners to estimate expected positive counts given fleet size and study window.

**What makes this extraordinary:** The gate PIVOT outcome is the contribution, not a calibration result. This inverts the typical paper structure, reporting a pre-registered negative feasibility finding as a primary contribution — a model for rigorous null-result research in security.

**Pre-registered claim cards (Q1/Q2/Q3)** tied to `STEP3_12_FIX_F3_METRIC_CLAIM_BINDING.md` demonstrate formal pre-registration of analysis before data examination.

---

## Paper 3: HygieneBench — Cyber-Hygiene Anomaly Detection Benchmark

### Full Title
HygieneBench: A Reproducible Synthetic Benchmark for Cyber-Hygiene Anomaly Detection Across Identity, Endpoint, and Patch Telemetry

### Submission Target
ACM CCS AISec Workshop (primary); IEEE S&P Workshop on Security Benchmarks (backup)

### Status
Packaging — submission-ready LaTeX at `paper3/submission/acm/`

### Technical Summary

Cyber-hygiene anomaly detection — identifying stale privileged accounts, dormant account reactivations, endpoint agent gaps, patch noncompliance clusters, and telemetry missingness — is operationally critical but has **no dedicated public benchmark**. Existing benchmarks (LANL, CERT, CICIDS, Mordor) focus on network intrusion or insider threat, not hygiene state.

**HygieneBench** is the first open benchmark covering:
- **11 synthetic entity/event tables:** Active Directory users, groups, computers, assets, login events, group membership events, account lifecycle events, endpoint patch state, vulnerability records, remediation events, telemetry freshness log
- **12 anomaly classes (AH-01 to AH-12):** stale privileged accounts, privilege drift, group membership drift, dormant reactivation, unusual logins, endpoint-identity correlation, patch noncompliance, KEV exposure aging, asset inventory mismatches, missing agents, telemetry missingness, remediation delays
- **7 evaluation tasks (T1–T7)** under **5 telemetry conditions** (baseline, fresh, stale, missing, unsupervised)
- **8 detection methods:** Rule baseline (M1), Hybrid scorer (M2), Isolation Forest (M3), LOF (M4), OCSVM (M5), Linear autoencoder (M6), Temporal z-score (M7), Graph-augmented IF (M8)

**Structural priors** from public sources: NIST NVD (CVE severity), Verizon DBIR 2026 (43-day critical patch lag), CISA BOD 23-01 (14-day asset discovery, 72-hour patch data cadence).

**Key results (810 evaluation runs, 3 seeds × 5 conditions × 7 tasks × 8 methods):**
- **86.2% failure rate:** 608 of 705 (condition, task, method) configurations fail to outperform the rule baseline by the pre-registered Δ ≥ 0.05 AP threshold in ≥ 2/3 seeds
- **ML adds value on exactly 2 of 7 tasks:** T2 (group membership drift, best ML: M7 temporal z-score, +0.185 AP) and T5 (patch/vulnerability hygiene, best ML: M5 OCSVM, +0.210 AP)
- **M8 (graph) fails on 100% of configs:** bipartite user-group graph topology provides no useful signal for temporal account-state tasks
- **Staleness degrades detection:** C-STALE produces −0.168 AP on T3 (endpoint–identity correlation), quantifying the operational cost of stale data pipelines

### Significance Statement

HygieneBench makes three contributions to benchmark practice in security:

1. **Task-stratified negative-result reporting:** 86.2% of configurations are failure-flagged under a pre-registered protocol — a finding that challenges the assumption that ML always improves on rule baselines for security anomaly detection
2. **Telemetry freshness as a first-class evaluation axis:** The benchmark is the first to model controlled staleness and missingness conditions, enabling researchers to quantify how data pipeline quality affects detection
3. **Open, reproducible synthetic generator:** All 15 dataset instances (5 conditions × 3 seeds) are generated from a seeded, open-source Python pipeline grounded in publicly citable structural priors — enabling exact reproduction and extension

**What makes this extraordinary:** No prior benchmark covers the joint space of AD identity hygiene, endpoint patch posture, vulnerability exposure, and telemetry freshness. This benchmark fills a genuine gap and provides the first rigorous evidence base for when ML adds value vs. when rule baselines suffice in hygiene monitoring.

---

## Paper 4: HygienePrio — Hygiene-Augmented Exploit-Weighted Scorer

### Full Title
HygienePrio: Cyber-Hygiene Signal Augmentation for EPSS-Weighted Vulnerability Prioritization

### Submission Target
IEEE Transactions on Network and Service Management (TNSM) (primary); ACM Digital Threats: Research and Practice (DTRAP) (backup)

### Status
In progress — submission-ready LaTeX at `paper4/submission/ieee/`; frozen results at `paper4/results/primary_results_v1/`

### Technical Summary

Paper 1 found that combining CVE-level signals (EPSS, CVSS, KEV status, asset criticality, network exposure) did not improve prioritization over EPSS alone when only CVE-level features were available. Paper 3 demonstrated that host-level hygiene signals — patch debt, Active Directory exposure breadth, and telemetry freshness — carry genuine discriminative structure in a realistic synthetic fleet. **HygienePrio** connects these two findings by introducing a host-level Hygiene Risk Score (HRS) and combining it with EPSS via a principled weighted scorer with an explicit interaction term.

**HygienePrio scoring formula:**

```
S(h, c) = α·EPSS(c) + β·HRS(h) + γ·KEV_recency(c) + δ·(EPSS(c) × HRS(h))
```

Where:
- `HRS(h) = 0.5·PatchPosture(h) + 0.3·ADExposure(h) + 0.2·TelemetryFreshness(h)`
- `KEV_recency(c) = exp(−0.05 × days_since_kev_entry)` for KEV CVEs, 0 otherwise
- Calibrated weights: α=0.7, β=0.5, γ=0.1, δ=0.2 (grid search on 5 held-out seeds)

**Key evaluation results (25 seeds; synthetic evaluation only):**
- **HygienePrio-full:** P@50 = 0.509 (BCa 95% CI: 0.480–0.542)
- **EPSS-only:** P@50 = 0.202 (BCa 95% CI: 0.174–0.236)
- **Improvement:** ~31 pp at P@50; non-overlapping BCa CIs; synthetic evaluation only
- **Ablation (leave-one-dimension-out):** noPatch −20 pp; noAD −9 pp; noFreshness −2 pp
- **Oracle-gap:** HygienePrio 49.1% vs. EPSS-only 79.8% — substantial reduction in distance from optimal prioritization
- **Ground-truth circularity:** HRS appears in both scorer and ground-truth label definition — explicitly disclosed and bounded in §9 (Threats to Validity)

### Significance Statement

HygienePrio is the first scorer to jointly optimize per-CVE exploit likelihood (EPSS) and host-level hygiene posture for (host, CVE) pair prioritization. The work closes the null-result loop from Paper 1: the missing signal was host-level hygiene, not additional CVE-level features. The 31 pp P@50 improvement (synthetic evaluation) is a strong positive result, but all claims are explicitly bounded to the synthetic evaluation context — generalization to real enterprise fleets is identified as future work requiring external validation.

**What makes this extraordinary:** HygienePrio completes a four-paper arc that is internally consistent and methodologically rigorous: Paper 1 establishes the benchmark and reports a null result; Paper 2 documents why public data cannot calibrate it; Paper 3 shows that hygiene signals carry discriminative structure; Paper 4 demonstrates that combining those hygiene signals with EPSS produces the first meaningful improvement. The arc models a complete research program — not just a single positive result, but an honest progression from null finding through causal investigation to positive contribution.

---

## Cross-Paper Coherence and Research Program

The four papers form a coherent research program with internal cross-referencing:

| Paper | Builds on | Enables |
|---|---|---|
| Paper 1 (VulnPrio) | EPSS, KEV, CVSS, NIST SP 800-40 | Paper 2 (calibration question); Paper 4 (null result to close) |
| Paper 2 (CalibScore) | Paper 1 benchmark infrastructure | Future calibration with richer labels |
| Paper 3 (HygieneBench) | Hygiene monitoring literature gap | Paper 4 (hygiene dimension design + HRS components) |
| Paper 4 (HygienePrio) | Paper 1 null result + Paper 3 hygiene signals | Future real-fleet validation; open scorer for community use |

**Common methodological thread:** All four papers share:
- Pre-registered analysis plans before examining results
- Honest null/negative-result reporting as a first-class contribution
- Fully synthetic seeded data (no production or employer data)
- Open reproducibility artifacts (generator, code, frozen results)
- Multiple-seed evaluation with BCa bootstrap CIs (Papers 1 and 4: also Wilcoxon + Holm)

---

## Compilation Instructions (for Attorneys/Petitioners)

All papers compile with [Tectonic](https://tectonic-typesetting.github.io/) (recommended) or pdfLaTeX + BibTeX:

```bash
# Using Tectonic (recommended — handles dependencies automatically)
tectonic "paper1-vuln-prioritization/paper/submission/ieee/main.tex"
tectonic "paper1-vuln-prioritization/paper2/submission/cset/main.tex"
tectonic "paper3/submission/acm/main.tex"
tectonic "paper4/submission/ieee/main.tex"
tectonic "eb1a_portfolio/exhibit_cover.tex"

# Merge all into portfolio PDF
python3 eb1a_portfolio/merge_portfolio.py
# → Output: eb1a_portfolio/EB1A_Research_Portfolio_Malla_2026.pdf (45 pages)
```

Requires: Tectonic (`brew install tectonic` on macOS) or MacTeX (macOS) or MiKTeX (Windows).

---

## Evidence Index for EB-1A Petition

| Exhibit | Type | Description |
|---|---|---|
| Exhibit A | Research paper | Paper 1 (VulnPrio) — IEEE-format LaTeX PDF (8 pp) |
| Exhibit B | Research paper | Paper 2 (CalibScore) — IEEE CSET-format LaTeX PDF (8 pp) |
| Exhibit C | Research paper | Paper 3 (HygieneBench) — ACM-format LaTeX PDF (7 pp) |
| Exhibit D | Research paper | Paper 4 (HygienePrio) — IEEE TNSM-format LaTeX PDF (11 pp) |
| Manuscript A | Working draft | Paper 1 full manuscript draft (.md) |
| Manuscript B | Working draft | Paper 2 full manuscript draft (.md) |
| Manuscript C | Working draft | Paper 3 full manuscript draft (.md) |
| Manuscript D | Working draft | Paper 4 full manuscript draft (.md) |
| Pre-reg B | Pre-registration | Paper 2 STEP4_PREREGISTRATION.md (8 stop rules, pre-data) |
| Pre-reg C | Pre-registration | Paper 3 PAPER3_DECISION_LOG.md (failure protocol, pre-data) |
| Pre-reg D | Pre-registration | Paper 4 PAPER4_PROTOCOL.md (HRS weights, grid, seeds, ground truth) |
| Audit B | Audit trail | Paper 2 audit/primary_complete.json (chunked API acquisition) |
| Data C | Benchmark data | Paper 3 results/primary_full_v1/ (810 evaluation runs) |
| Data D | Benchmark data | Paper 4 results/primary_results_v1/primary_results.csv (225 rows) |
| Code A | Code artifacts | Paper 1 src/ (scheduler, audit log, reproducibility harness) |
| Code D | Code artifacts | Paper 4 src/hygieneprio/ (HRS, scorer, EEHDA generator) |

**Merged portfolio PDF:** `eb1a_portfolio/EB1A_Research_Portfolio_Malla_2026.pdf` — 45 pages, 993 KB
(Cover pages: 11 pp · Paper 1: 8 pp · Paper 2: 8 pp · Paper 3: 7 pp · Paper 4: 11 pp)

---

*This portfolio was self-assembled by the researcher. All claims in this document are documented with traceable artifacts in the research directories. No employer data, government operational data, or production system data was used in any paper.*
