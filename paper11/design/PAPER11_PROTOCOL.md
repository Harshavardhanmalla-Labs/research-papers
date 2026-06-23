# Paper 11: Pre-Registration and Research Protocol

**Title:** Context-Aware Vulnerability Prioritization for Government Endpoint Fleets
**Short title:** Context-Aware Prioritization for Government (CAP-G)
**Author:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management (TNSM) / government practitioner track
**Pre-registration date:** 2026-06-19
**Protocol version:** 1.0
**Date locked:** 2026-06-19 (before any CAP-G evaluation-seed result was inspected)
**Builds on:** Paper 4 (HygienePrio, host-hygiene-augmented EPSS ranking), Paper 6
(Capacity-Indexed Decay), and the real CVE/EPSS/KEV corpus in `real_data/processed/`
(snapshot 2026-06-05; 203,174 CVEs ≥ 2020; KEV prevalence 0.52%).

---

## 1. Motivation

HygienePrio (Paper 4) ranks each applicable `(host h, CVE c)` pair by a blend of
exploit likelihood (EPSS), host hygiene (HRS), and KEV recency. It treats every
host as **equally important to remediate**: a CVE on a training-room kiosk and the
same CVE on a Criminal Justice Information Services (CJIS) domain controller in a
DMZ receive the same host-side weight beyond their hygiene posture.

Government endpoint fleets are **mission-heterogeneous**. Federal and state security
guidance is explicit that remediation should be risk-prioritized by asset context:

- **NIST FIPS 199 / SP 800-60** categorize information systems by impact level
  (Low / Moderate / High) across confidentiality, integrity, and availability.
- **CISA BOD 22-01 / 23-01** direct agencies to remediate Known Exploited
  Vulnerabilities on a timeline driven by exposure and asset role.
- **CJIS Security Policy v5.9** imposes elevated controls on systems handling
  criminal-justice information.
- **NIST SP 800-53 RA-5** requires vulnerability remediation prioritized by
  organizational risk, not raw severity.

None of Papers 1-10 model asset context (criticality tier, network exposure zone,
data sensitivity) as a first-class ranking signal. Paper 11 asks whether adding a
pre-registered **Asset Context Score (ACS)** to the HygienePrio ranking improves
the prioritization of *mission-critical* exposure under a fixed remediation capacity
`K`, and, critically, what that improvement **costs** on the context-blind metric
HygienePrio was optimized for.

This is an applied, government-facing paper. Its contribution is honest
characterization, not a claim that context-awareness is free.

---

## 2. Research Questions

**RQ1, Primary.** Does adding a pre-registered Asset Context Score to HygienePrio
improve **Mission-Weighted Precision@K** (MWP@K, §6.1) over the context-blind
HygienePrio baseline, across remediation capacities K = 50, 100, 250?

**RQ2, Regime dependence.** Is any MWP@K advantage capacity-dependent? Following
Paper 6 (capacity-indexed decay), we expect the advantage to shrink as K grows,
because at large K the capacity budget absorbs most high-priority pairs regardless
of ordering.

**RQ3, Mechanism (heterogeneity).** Is any advantage actually attributable to
fleet *heterogeneity* in asset context? On a homogeneous fleet (all assets equal
context), context weighting should provide no benefit. If it still does, the claimed
mechanism is wrong.

**RQ4, Honest tradeoff.** Does context-awareness *cost* generic precision? We expect
CAP-G to sacrifice context-blind Precision@K (the HygienePrio target) in exchange for
mission precision. Quantifying that tradeoff is a primary deliverable.

**RQ5, Ablation.** Which context dimension, criticality tier, network zone, or data
sensitivity, carries the largest marginal contribution to MWP@K?

---

## 3. Hypotheses

**H1 (Primary).** Mean MWP@K of CAP-G-full exceeds context-blind HygienePrio by at
least **5 percentage points (pp)** averaged across K = 50, 100, 250 and across all 25
evaluation seeds:
`mean(MWP@K_CAP-G) - mean(MWP@K_HygienePrio) ≥ 0.05`.

**H2 (Regime dependence).** The MWP@K advantage decreases monotonically in K:
`Δ@50 > Δ@100 > Δ@250`, where `Δ@K = MWP@K_CAP-G - MWP@K_HygienePrio`.

**H3 (Mechanism / heterogeneity).** On a **homogeneous** control fleet (every host
assigned identical asset context), the CAP-G advantage collapses to within **1 pp**
of zero at K = 50: `|Δ@50_homogeneous| ≤ 0.01`. A larger residual advantage on the
homogeneous fleet **falsifies** the heterogeneity mechanism.

**H4 (Honest tradeoff).** CAP-G-full achieves **lower or equal** *context-blind*
Precision@K than HygienePrio at K = 50:
`P@50_blind(CAP-G) ≤ P@50_blind(HygienePrio) + 0.01`.
If CAP-G were to win on *both* the mission metric and the context-blind metric, that
would indicate a metric or labelling artifact and trigger the investigation rule in §8.

**Rationale for H1.** HygienePrio's host weight (HRS) reflects *hygiene risk*, not
*mission value*. A poorly-patched kiosk can out-rank a well-patched CJIS controller
under HygienePrio. Injecting ACS re-weights toward mission value, which by
construction aligns the ranking with the mission-weighted ground truth (§5). The
open empirical question is the *magnitude* and its capacity dependence, not the sign.

**Rationale for H4.** The mission-weighted ground truth and the context-blind ground
truth reward different orderings. A ranker tuned for one should not dominate the
other; an honest context-aware method trades generic precision for mission precision.
H4 pre-commits us to reporting that cost even if it is unflattering.

---

## 4. Asset Context Model

Each host `h` is assigned three context attributes by the government fleet generator
(§5.1), with categorical values mapped to normalized severities in `[0, 1]`. The
category mixes are **structural priors grounded in public guidance**, not employer
data.

### 4.1 Asset criticality tier (FIPS 199 impact level)

| Tier | Value | Fleet share | Examples |
|---|---|---|---|
| MISSION_CRITICAL | 1.00 | 5%  | Domain controllers, CJIS app servers, emergency dispatch |
| HIGH             | 0.70 | 20% | General servers, privileged admin workstations |
| MEDIUM           | 0.40 | 50% | Standard staff workstations |
| LOW              | 0.15 | 25% | Kiosks, training-room, guest endpoints |

### 4.2 Network exposure zone

| Zone | Value | Fleet share |
|---|---|---|
| INTERNET_FACING | 1.00 | 8%  |
| DMZ             | 0.75 | 12% |
| INTERNAL        | 0.40 | 65% |
| ISOLATED        | 0.10 | 15% |

### 4.3 Data sensitivity (CJIS / CUI)

| Sensitivity | Value | Fleet share |
|---|---|---|
| CJIS    | 1.00 | 15% |
| PII_CUI | 0.60 | 45% |
| PUBLIC  | 0.20 | 40% |

### 4.4 Asset Context Score (ACS)

```
ACS(h) = c1 · crit(h) + c2 · zone(h) + c3 · sens(h)
```

Pre-registered dimension weights (criticality-dominant, mirroring the FIPS 199
emphasis on system categorization and the HRS weighting precedent in Paper 4):
**c1 = 0.5, c2 = 0.3, c3 = 0.2.** These are fixed from priors and are NOT tuned on
any seed.

**Robustness variant (pre-registered, secondary):** `ACS_hwm(h) = max(crit, zone,
sens)`, a "high-water-mark" aggregation matching FIPS 199's literal max rule. Reported
as a robustness check on H1; not the primary aggregation.

---

## 5. Method

### 5.1 Government fleet generator

The EEHDA synthetic fleet generator (Papers 1/3/4) is extended with a **context
layer** that assigns each host the three attributes in §4 from the fixed category
mixes. The base fleet (hosts, users, groups, vulnerability records, telemetry) and
all CVE attributes are generated exactly as in Paper 4, then CVE `epss`/`in_kev`
fields are **resampled from the real corpus** (`real_data/processed/cve_corpus_for_sampling.csv`)
using the Paper-10 resampling procedure, so exploit signal reflects the real EPSS/KEV
distribution. Context assignment is independent of CVE attributes (no leakage between
ACS and EPSS).

Fleet scale: ~830 hosts, ~3,500 (host, CVE) pairs per seed (Paper 4 medium scale).

### 5.2 CAP-G scorer

```
S_CAP-G(h, c) = S_HygienePrio(h, c) · (1 + ρ · ACS(h))
```

where `S_HygienePrio` is the calibrated Paper-4 scorer (α=0.7, β=0.5, γ=0.1, δ=0.2,
unchanged and re-used verbatim) and `ρ ≥ 0` is the **context-emphasis** hyperparameter.

### 5.3 Hyperparameter calibration

`ρ` is calibrated by grid search on **5 held-out calibration seeds** (11, 22, 33, 44,
55, disjoint from evaluation seeds), grid `ρ ∈ {0.5, 1, 2, 4, 8}`, objective = mean
MWP@50 on calibration seeds. The selected `ρ` is **fixed before** the primary
evaluation on the 25 evaluation seeds. The calibration-set result is reported
separately and cannot retroactively modify this protocol. All other weights (scorer
α…δ, HRS w1…w3, ACS c1…c3) are fixed from priors and not tuned.

---

## 6. Metrics

### 6.1 Primary metric, Mission-Weighted Precision@K (MWP@K)

A pair `(h, c)` is a **Mission-Critical True Positive (MCTP)** iff:

```
EPSS(c) > 0.10   AND   ACS(h) > fleet 75th percentile
```

`MWP@K = |{MCTP in top-K}| / K`, computed at K = 50, 100, 250.

This mirrors HygienePrio's ground-truth structure (Paper 4 §4.1: `EPSS>0.10 AND
HRS>P75`) but replaces hygiene risk with mission context, the operationally correct
target for a government fleet, pre-registered and not adjusted post-hoc.

### 6.2 Secondary metrics

- **Context-blind Precision@K (P@K_blind):** the *original* HygienePrio ground truth
  (`EPSS>0.10 AND HRS>P75`). Used to quantify the H4 tradeoff.
- **Criticality-Weighted Exposure Reduction (CWER@K):** continuous mission-risk
  capture, `Σ_{top-K} ACS(h)·1[EPSS(c)>0.10]` normalized by the oracle top-K sum.
- **NDCG@K** on MCTP labels (rank-position-weighted mission precision).

### 6.3 Reporting

All metrics reported as mean ± 95% BCa bootstrap CI (10,000 resamples) across 25
evaluation seeds, reusing the Paper-4 `metrics.bca_ci_mean` implementation. Evidentiary
standard is **BCa CI non-overlap**, consistent with Papers 1, 3, 4. No NHST p-values.

---

## 7. Baselines

All methods rank the identical `(h, c)` universe per seed:

| Method | Description |
|---|---|
| **EPSS-only** | EPSS(c) desc; CVSS tiebreak. |
| **CVSS-only** | CVSS base desc. |
| **Random** | Uniform random, seed-fixed. |
| **HRS-only** | Host hygiene only (Paper 4 baseline). |
| **Context-only** | Rank by ACS(h) alone (no exploit signal), tests whether context without EPSS suffices; expected insufficient. |
| **HygienePrio** | Calibrated Paper-4 scorer, context-blind. **Primary comparison.** |
| **CAP-G-full** | S_HygienePrio · (1 + ρ·ACS). **Proposed method.** |
| **CAP-G-noCrit** | ACS with c1 = 0 (criticality removed). Ablation (RQ5). |
| **CAP-G-noZone** | ACS with c2 = 0 (zone removed). Ablation (RQ5). |
| **CAP-G-noSens** | ACS with c3 = 0 (sensitivity removed). Ablation (RQ5). |
| **CAP-G-hwm** | ACS_hwm (high-water-mark). Robustness variant. |

---

## 8. Failure Criteria & Investigation Rules

**H1 null.** If `mean MWP@K_CAP-G - mean MWP@K_HygienePrio < 0.02` across all three K
on evaluation seeds, declare H1 null. Action: report as a null result; pivot the
primary contribution to the tradeoff characterization (RQ4) and ablation (RQ5).
**Do not** add post-hoc context dimensions or re-define ACS to manufacture a positive.

**H3 falsification.** If the homogeneous-fleet advantage exceeds 1 pp at K = 50, report
the heterogeneity mechanism as **falsified** and investigate whether the gain is a
labelling artifact (MCTP definition shares the ACS term with the scorer).

**H4 violation (investigation rule).** If CAP-G wins on *both* MWP@K and context-blind
P@K, halt and audit the ground-truth construction for circularity before reporting any
positive H1 result. A method cannot legitimately dominate two metrics that reward
opposing orderings.

**Calibration stop.** If the best `ρ` on calibration seeds does not raise MWP@50 over
HygienePrio by ≥ 3 pp, halt grid expansion and report the calibration result alongside
the (expected null) evaluation result. Do not expand the grid to chase a positive.

**Data integrity.** If any seed yields < 50 MCTP pairs (MWP@50 degenerate), exclude and
document it. If > 5 of 25 evaluation seeds are excluded, halt and report a generation
failure.

---

## 9. Pre-Registration Attestation

This protocol was written **before** any experimental result was generated on the 25
evaluation seeds (200-224). The `ρ` calibration on the 5 held-out seeds (11, 22, 33,
44, 55) is permitted to precede full evaluation; that result is documented separately
and cannot cause retroactive modification of any hypothesis, threshold, or metric
definition above.

- **Evaluation seeds:** 200-224 (25 seeds)
- **Calibration seeds:** 11, 22, 33, 44, 55 (5 seeds, held out)
- **Protocol locked:** 2026-06-19
- **No real employer/operational data** is used at any stage. The CVE EPSS/KEV corpus
  is the public FIRST EPSS + CISA KEV snapshot already vendored in `real_data/`.
