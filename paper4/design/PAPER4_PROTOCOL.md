# Paper 4 — HygienePrio: Pre-Registration / Research Protocol

**Title:** HygienePrio: Cyber-Hygiene Signal Augmentation for EPSS-Weighted Vulnerability Prioritization  
**Short title:** HygienePrio  
**Pre-registration date:** 2026-05-31  
**Protocol version:** 1.0  
**Status:** Pre-registered (internal)

---

## 1. Research Questions

**RQ1 — Primary:** Do host-level cyber-hygiene signals (patch posture, Active Directory exposure state, telemetry freshness) improve Precision@K over an EPSS-only baseline in a capacity-constrained vulnerability remediation simulation?

**RQ2 — Ablation:** Which hygiene dimension(s) contribute most to any observed improvement? Specifically, does patch posture, AD exposure state, or telemetry freshness carry the largest marginal contribution to Precision@K when each is removed in a leave-one-out ablation?

**RQ3 — Consistency:** Is any improvement in Precision@K consistent across remediation capacity budgets K = 50, 100, and 250 (host, CVE) pairs? Or does gain appear only at small K (high-priority triage mode) and diminish at larger K?

---

## 2. Hypotheses

**H1 (Primary):** HygienePrio Precision@K is higher than the EPSS-only baseline by at least 5 percentage points (pp) on average across K = 50, 100, 250 and across all 30 evaluation seeds. Equivalently: mean(P@K_HygienePrio) − mean(P@K_EPSS) ≥ 0.05.

**H2 (Ablation):** The patch posture dimension has the highest marginal contribution to Precision@K among the three hygiene dimensions, measured as the drop in mean P@K when that dimension is removed from HRS.

**Rationale for H1:** Paper 1 (VulnPrio) found that adding CVE-level features (asset criticality, endpoint exposure, KEV flags) did not improve over EPSS-only; the multi-factor model was statistically indistinguishable from the EPSS baseline. We hypothesize that the missing signal is not additional CVE-level features but rather host-level hygiene posture (particularly whether a host is actively managed, freshly telemetered, and has low residual patch debt). HygienePrio tests this hypothesis directly by injecting HygieneBench-derived host-level scores.

**Rationale for H2:** HygieneBench (Paper 3) found that patch-vulnerability hygiene (Task T5) was one of only two tasks where ML methods added meaningful signal over the rule baseline (+0.210 AP for OCSVM). This suggests patch posture carries discriminative information that rule-based signals fail to fully capture. We expect this to translate into higher marginal contribution in the ablation.

---

## 3. Method Overview

### 3.1 HygienePrio Scorer Architecture

The HygienePrio scorer assigns a priority score S(h, c) to each (host h, CVE c) pair. The scorer has four components:

```
S(h, c) = α × EPSS(c)
         + β × HRS(h)
         + γ × KEV_recency(c)
         + δ × (EPSS(c) × HRS(h))
```

where:

- `EPSS(c)` — EPSS probability score for CVE c, drawn from the synthetic fixture (range [0, 1])
- `HRS(h)` — Hygiene Risk Score for host h (see §3.2), normalized to [0, 1], higher = worse hygiene = higher priority
- `KEV_recency(c)` — KEV recency weight for CVE c (see §3.3), range [0, 1]
- `EPSS(c) × HRS(h)` — interaction term: a host with poor hygiene on a CVE with high exploit probability receives extra weight
- `α, β, γ, δ` — non-negative weights calibrated by grid search (see §3.4)

### 3.2 Hygiene Risk Score (HRS)

HRS(h) is a normalized, weighted combination of three hygiene dimensions derived from the HygieneBench synthetic fleet schema:

```
HRS(h) = w1 × PatchPosture(h) + w2 × ADExposure(h) + w3 × TelemetryFreshness(h)
```

- **PatchPosture(h):** Proportion of open (unpatched) CVEs on host h relative to total applicable CVEs. Higher = more unpatched = higher hygiene risk.
- **ADExposure(h):** Active Directory exposure index: captures group membership breadth (number of AD groups containing h's primary user account), privileged account exposure flag, and whether h hosts domain-privileged processes. Normalized by fleet-wide max.
- **TelemetryFreshness(h):** Staleness score derived from the `telemetry_freshness_log` table. Computed as days since last successful telemetry check-in, capped at 30 days and normalized. Higher staleness = less visibility = higher hygiene risk.

Default dimension weights before calibration: w1 = 0.5, w2 = 0.3, w3 = 0.2. Final weights determined by held-out grid search.

### 3.3 KEV Recency Weight

KEV_recency(c) uses an exponential decay on the number of days since CVE c was added to the CISA KEV catalog:

```
KEV_recency(c) = exp(−λ × days_since_kev_entry(c))   if c ∈ KEV
               = 0                                      if c ∉ KEV
```

Default decay constant: λ = 0.05 (half-life ~14 days). If c is not in KEV, it receives no KEV recency weight; its prioritization then depends on EPSS and HRS only.

### 3.4 Weight Calibration

Weights (α, β, γ, δ) and KEV decay λ are calibrated by grid search on a held-out calibration set of 5 of the 30 seeds (seeds not used in primary evaluation). The grid is:

- α ∈ {0.3, 0.5, 0.7, 1.0}
- β ∈ {0.1, 0.3, 0.5, 0.7}
- γ ∈ {0.0, 0.1, 0.3, 0.5}
- δ ∈ {0.0, 0.1, 0.2, 0.3}
- λ ∈ {0.02, 0.05, 0.10}

Objective: maximize mean P@50 on calibration seeds. The selected weight combination is fixed before primary evaluation on the remaining 25 seeds.

### 3.5 Ranked List Generation

For each seed, all (h, c) pairs in the fleet's vulnerability exposure table are scored by S(h, c). Pairs are sorted descending by S(h, c). Evaluation cuts the ranked list at K = 50, 100, and 250.

---

## 4. Dataset

### 4.1 Synthetic Fleet

- **Generator:** EEHDA (Extended Enterprise Hygiene Dataset Artifact) synthetic fleet generator — the same codebase used in Papers 1 and 3, extended to output HygieneBench-compatible hygiene tables alongside the VulnPrio vulnerability-host pair tables.
- **Fleet size:** Approximately 830 hosts, 1,000 user accounts, ~3,500 vulnerability records per seed (consistent with HygieneBench medium scale).
- **Seed count:** 30 seeds total. 5 calibration seeds (held-out for weight calibration). 25 evaluation seeds (primary results).
- **CVE fixture:** Synthetic CVE records with EPSS scores drawn from NVD-distribution priors and KEV membership sampled at 8% prevalence (consistent with Paper 1 fixture).
- **Ground truth:** "True positive" pairs are defined as (h, c) pairs where h has poor hygiene (HRS > fleet 75th percentile) AND c has EPSS > 0.10 AND c is applicable to h. This definition is pre-registered; it is not adjusted post-hoc.

### 4.2 No Real Data

No employer data, production fleet data, patient data, or operational data is used at any stage. All data is synthetically generated with documented structural priors consistent with Papers 1 and 3.

---

## 5. Baselines

The following methods are evaluated on identical ranked-list generation from the same (h, c) pair universe:

| Baseline ID | Description |
|---|---|
| **EPSS-only** | Sort (h, c) pairs by EPSS(c) descending. Ties broken by CVSS base score. Primary comparison baseline. |
| **CVSS-only** | Sort (h, c) pairs by CVSS base score descending. Ties broken randomly (seed-fixed). |
| **Random** | Uniform random ranking of (h, c) pairs (seed-fixed). |
| **HRS-only** | Sort (h, c) pairs by HRS(h) descending. Ties broken by EPSS(c). Tests whether host hygiene alone (without exploit likelihood) is sufficient. |
| **HygienePrio-full** | Full scorer S(h,c) as described in §3.1, with calibrated weights. |
| **HygienePrio-noInteraction** | S(h,c) with δ = 0 (no interaction term). Tests whether the cross-term adds beyond additive combination. |
| **HygienePrio-noPatch** | HRS computed with w1 = 0 (patch posture omitted). Ablation for RQ2. |
| **HygienePrio-noAD** | HRS computed with w2 = 0 (AD exposure omitted). Ablation for RQ2. |
| **HygienePrio-noFreshness** | HRS computed with w3 = 0 (telemetry freshness omitted). Ablation for RQ2. |

---

## 6. Metrics

### 6.1 Primary Metric

**Precision@K:** Proportion of true positive (h, c) pairs in the top-K ranked list. Computed for K = 50, 100, 250.

```
P@K = |{(h,c) in top-K : (h,c) is true positive}| / K
```

### 6.2 Secondary Metrics

**NDCG@K (Normalized Discounted Cumulative Gain at K):** Standard ranking quality metric that weights higher-ranked positives more. Computed at K = 50, 100, 250.

**Oracle-gap (%):** How much of the theoretically achievable P@K does each method capture?

```
Oracle-gap(method, K) = (P@K_oracle − P@K_method) / P@K_oracle × 100
```

where P@K_oracle is the P@K achieved by an oracle that knows all true positives and ranks them first.

### 6.3 Reporting

All metrics reported as mean ± 95% bootstrap confidence interval (BCa, 10,000 resamples) across 25 evaluation seeds. No NHST p-values are reported; the protocol relies on BCa CI non-overlap as the evidentiary standard, consistent with Papers 1 and 3.

---

## 7. Failure Criteria

**Primary failure criterion (for H1):** If mean P@K_HygienePrio − mean P@K_EPSS-only < 0.02 (2 pp) across all three K values (K = 50, 100, 250) on evaluation seeds, the result is declared null for H1.

**Action on primary null result:** Report as a null result in the null-result section. Pivot the primary contribution to the ablation analysis (RQ2, RQ3), characterizing which hygiene dimensions do and do not add signal, following the honest reporting approach of Papers 1 and 3. Do not add post-hoc features or re-define the scorer architecture to achieve a positive result.

**Ablation failure (for H2):** If all three dimension ablations (noPatch, noAD, noFreshness) produce indistinguishable P@K (BCa CIs overlapping for all three), report H2 as indeterminate.

---

## 8. Stop Rules

**Stop and report null:** If the held-out calibration grid search yields a best weight combination where P@50 on calibration seeds does not exceed EPSS-only by at least 3 pp, halt grid search expansion. Do not expand the grid or add features to chase the positive result. Report the calibration-set result alongside the evaluation result.

**Stop and report data integrity failure:** If any seed produces fewer than 50 true positive pairs (making P@50 undefined or degenerate), that seed is excluded and documented. If more than 5 of 25 evaluation seeds are excluded, halt and report a data generation failure.

**Stop and report interaction term null:** If the HygienePrio-noInteraction variant achieves P@K within 1 pp of HygienePrio-full for all K, the interaction term is declared uninformative and dropped from the final model description. This is a planned simplification stop, not a failure.

---

## 9. Pre-Registration Attestation

This protocol was written before any experimental results were generated on the 25 evaluation seeds. The calibration grid search result on 5 held-out seeds may already exist at time of pre-registration; that result must be documented separately and cannot cause retroactive modification of this protocol.

**Protocol locked:** 2026-05-31  
**Protocol author:** [Author Name]  
**Review status:** Internal pre-registration; not submitted to OSF or AsPredicted at this stage.
