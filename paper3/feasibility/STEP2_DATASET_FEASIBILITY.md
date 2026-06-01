# Paper 3 — Step 2: Dataset Feasibility Report

**Date:** 2026-05-28
**Status:** Complete
**Feeds into:** `SCHEMA_v0_1.md`, `PAPER3_DECISION_LOG.md`

---

## Purpose

Evaluate whether Paper 3 can be built using fully synthetic telemetry, confirm or rule out the availability of publicly citable structural priors for each schema component, establish the synthetic generation strategy, and explicitly reconfirm distinctness from Paper 1 and Paper 2.

---

## 1. Data Strategy

**Selected approach: Option A (fully synthetic) with Option C structural priors (public statistics as calibration anchors).**

- All telemetry is synthetic and seeded.
- No employer logs, no ADOT data, no real account or device names.
- Structural priors (where available) are cited published statistics used to set plausible parameter ranges for the synthetic generator; they are not used as raw training data.
- Where published structural priors are unavailable (e.g., AD group-size distributions), parameter ranges are chosen conservatively and disclosed as model assumptions with sensitivity sweeps.

**Realism caveat (mandatory disclosure in the paper):** Synthetic telemetry replicates the *structure* and *statistical shape* of real operational telemetry, not its content. Claims about detection performance are bounded to the synthetic evaluation environment. Generalization to real deployments is explicitly stated as future work.

---

## 2. Structural Priors Assessment — Per Schema Domain

### 2.1 Active Directory: Group Sizes and Account Counts

**Prior availability: NOT FOUND as a formal published study.**

Research confirmed: no peer-reviewed paper or publicly available empirical dataset publishes typical enterprise AD group-size distributions, account counts, or OU-depth statistics.

**What exists:**
- Microsoft technical documentation references architectural limits (e.g., 5,000-member TokenGroup default limit; 1,024 SID token limit). `[CONFIRMED-DOC]`
- Practitioner blog posts (e.g., Sean Metcalf / adsecurity.org) describe patterns anecdotally. `[CONFIRMED-TOOL]` — not citable as a primary reference.
- BloodHound data from public GitHub-shared community datasets shows real AD topologies but is not a controlled statistical study.

**Decision: Use documented architecture limits + reasonable assumptions. Disclose explicitly.**

Synthetic generator defaults (to be documented in SCHEMA_v0_1.md and the paper's supplemental):
- Population: 500–5,000 users (configurable).
- Groups: 10–200 groups (varying by population scale).
- Privileged group membership rate: 2–8% of accounts (to be swept).
- Stale account rate: 5–20% (swept; a key experimental variable).
- Account lifecycle rate (creation/deletion/reactivation per month): 0.5–2% of population.

**Sensitivity sweep:** Vary these rates across the benchmark conditions. Findings reported relative to the parameter configuration, not to a "real AD."

---

### 2.2 Endpoint Patch Posture: Patch-Lag Distributions

**Prior availability: PARTIAL.**

**What exists:**
- Verizon DBIR 2026: average remediation time for critical vulnerabilities = **43 days**; ~25% of critical vulnerabilities patched within observation window. `[CONFIRMED — DBIR 2026]`
- Federal policy baselines (U.S.): 30-day distribution start, 90-day completion requirement for critical patches. CISA BOD 22-01 and agency-specific directives. `[CONFIRMED-DOC]`
- NIST SP 800-40 Rev. 4: defines patch management lifecycle stages and recommended timelines. `[CONFIRMED-DOC]`

**What does NOT exist (confirmed gap):** Granular, percentile-level patch-lag distributions (e.g., 25th/50th/75th/95th percentile patch-apply time by severity class) from peer-reviewed academic literature.

**Decision: Use DBIR 2026 aggregate statistics as loose shape anchors; model patch lag with a right-skewed distribution (log-normal or Weibull) consistent with the 43-day mean. Disclose assumption explicitly. Sweep distribution parameters.**

Synthetic generator patch-lag parameters:
- Critical (CVSS ≥ 9.0): mean lag 10–43 days, right tail up to 180 days.
- High (CVSS 7.0–8.9): mean lag 20–60 days.
- Medium (CVSS 4.0–6.9): mean lag 45–120 days.
- Low: mean lag 90–365 days.
- Per-machine patch-compliance rate: 60–95% (swept).
- Missing/offline endpoint rate (no recent heartbeat): 5–20% (swept; key for telemetry-freshness tasks).

---

### 2.3 Vulnerability Records: CVE Age and Severity Distributions

**Prior availability: HIGH. NVD is a fully public, citable database.**

**What exists:**
- NVD (National Vulnerability Database), https://nvd.nist.gov/. `[CONFIRMED-DOC]`
- NVD API and bulk data feeds provide: CVE publication dates, CVSS scores (v2, v3, v4), KEV flag (via CISA KEV list), CWE categories, affected product information.
- Empirical distributions of CVE age, severity, and KEV status can be computed directly from NVD bulk data and cited accordingly.
- CISA KEV catalog: https://www.cisa.gov/known-exploited-vulnerabilities-catalog. `[CONFIRMED-DOC]`

**Decision: Use NVD severity and age distributions as primary structural priors. Sample CVEs (with no employer-specific asset linkage) or use synthetic CVE-analogs with NVD-shaped parameters.**

Synthetic generator CVE parameters:
- CVSS score distribution: shaped to match NVD empirical distribution (right-skewed toward medium severity).
- KEV rate: ~5% of in-scope CVEs flagged as KEV (approximate from CISA KEV count vs. NVD total). `[VERIFY — confirm current rate]`
- CVE-to-patch latency: per 2.2 above.
- CVE per asset: 0–50 open CVEs depending on patch lag and asset OS profile.

---

### 2.4 Asset Inventory: Criticality and Ownership

**Prior availability: LOW as a formal study. Uses architecture assumptions.**

No peer-reviewed paper provides enterprise asset criticality distribution statistics (proportion of assets rated critical vs. high vs. medium).

**Decision: Use a configurable criticality distribution; default 5–15% of assets rated critical, 20–30% high, remainder medium/low. Disclose as a model assumption. Sweep criticality rate.**

Schema parameters:
- Asset criticality levels: critical / high / medium / low.
- Network segments: e.g., DMZ / workstation / server / privileged / OT-adjacent (configurable).
- Asset owner org-unit: maps to AD organizational unit.

---

### 2.5 Telemetry Freshness and Source Missingness

**Prior availability: PARTIAL.**

**What exists:**
- CISA BOD 23-01 mandates asset discovery every 7 days and vulnerability enumeration every 14 days for federal agencies. `[CONFIRMED-DOC]` — provides a policy anchor for "expected" freshness cadence.
- No published study of actual telemetry staleness rates in operational SOC environments.
- CISA risk assessments and FISMA IG reports mention "incomplete asset inventory" and "missing endpoint agent" findings, but without quantitative distributions. `[CONFIRMED-DOC — FISMA IG reports exist; exact figures not available without specific report citation]`

**Decision: Model freshness as configurable staleness decay; use BOD 23-01 cadences as the "normal" baseline and sweep decay rates as the experimental variable. Disclose explicitly.**

Schema parameters:
- Telemetry sources: AD events, EDR agent, patch management, vulnerability scanner, asset inventory.
- Per-source freshness interval (normal): 1–14 days depending on source.
- Staleness injection: none / mild (1–2× normal interval) / heavy (3–10× normal interval).
- Source-level missingness injection: none / one source / two sources / systematic OU-level gap.

---

### 2.6 Login Events and Identity Behavior

**Prior availability: LOW as formal published distributions. Uses operational assumptions.**

No published empirical study of enterprise login frequency distributions, off-hours login rates, or failed-login rates is available.

**Decision: Use conservative, documented assumptions. Sweep login-pattern parameters. Frame behavioral thresholds as benchmark-relative, not real-world-absolute.**

Schema parameters:
- Login events per user per day: Poisson(λ = 3–10) during business hours; near-zero off-hours except for anomalous injection.
- Failed login rate: 0.5–5% of attempts (configurable).
- Cross-subnet login rate: 1–10% of sessions (configurable).
- Anomaly injection: impossible location (cross-subnet beyond normal range), off-hours reactivation, velocity spike.

---

### 2.7 Remediation Events

**Prior availability: LOW as formal published distributions.**

**Decision: Derive from patch-lag parameters (§2.2). Remediation event schema is internal to the synthetic generator; no external prior required beyond patch-lag shape.**

Schema parameters:
- Remediation latency: drawn from the patch-lag distribution per §2.2.
- Remediation outcome: patched / deferred / false-closed / unresolved.
- Remediation actor: automated vs. manual (configurable rate).

---

## 3. Synthetic Generation Strategy

**Generator architecture (conceptual — code deferred to Step 3 per research plan):**

```
SyntheticHygieneGenerator(
  seed: int,
  population: PopulationConfig,       # users, groups, computers, assets
  lifecycle: LifecycleConfig,         # account create/disable/reactivate rates
  patch: PatchConfig,                 # lag distribution, compliance rate
  vulnerability: VulnConfig,          # CVE severity mix, KEV rate, per-asset count
  telemetry: TelemetryConfig,         # source freshness intervals, missingness regime
  anomaly: AnomalyInjectionConfig     # anomaly class list, injection rate, label schema
) -> SyntheticHygieneDataset
```

**Key design requirements:**
1. Fully deterministic given seed. Re-running with same seed produces byte-identical output.
2. Configurable population scale (small: 200 users; medium: 1,000; large: 5,000).
3. Anomaly injection is additive: baseline clean telemetry is generated first; anomalies are injected into a copy.
4. Each injected anomaly carries a ground-truth label (class, severity, timestamp, entity IDs).
5. Train/validation/test splits are fixed by seed; no data leaks across splits.
6. Dataset cards produced at generation time: population parameters, anomaly injection counts per class, class imbalance ratios, telemetry freshness regime, missingness regime.

---

## 4. Dataset Card Specification (Template)

Each generated dataset freeze carries a card with the following fields:

```
dataset_id: {generator_version}_{seed}_{population_scale}_{freshness_regime}_{missingness_regime}
generator_version: v0.1
seed: int
population_scale: small | medium | large
users_count: int
groups_count: int
computers_count: int
assets_count: int
patch_compliance_rate: float
telemetry_freshness_regime: none | mild | heavy
source_missingness_regime: none | one_source | two_sources | systematic_ou
anomaly_injection_summary:
  - class: str
    count: int
    prevalence: float
class_imbalance_ratios: dict[str, float]
train_entity_count: int
val_entity_count: int
test_entity_count: int
split_seed: int
generation_timestamp: ISO-8601
structural_prior_sources:
  patch_lag: "DBIR 2026 aggregate (43-day mean critical); model assumption log-normal"
  cve_severity: "NVD empirical distribution (public)"
  ad_group_size: "Model assumption; no published distribution; sensitivity swept"
  telemetry_cadence: "CISA BOD 23-01 (7/14-day mandate as normal baseline)"
```

---

## 5. Distinctness Reconfirmation — Paper 1 and Paper 2

### 5.1 Distinctness from Paper 1

| Dimension | Paper 1 | Paper 3 |
|---|---|---|
| Unit of analysis | Vulnerability × host *pair* | Entity *state record* across identity / endpoint / patch |
| Primary task | Ranking/prioritizing vulnerability–host pairs | Detecting anomalies in multi-domain hygiene state |
| Benchmark data | Endpoint-shaped vulnerability/host synthetic data | Identity + endpoint + patch + vulnerability + telemetry freshness synthetic data |
| Methods | Supervised ranking / CVSS-adjustment / ensemble | Unsupervised anomaly detection (Isolation Forest, LOF, OCSVM, autoencoder, graph) |
| Key contribution | Reproducible vulnerability prioritization benchmark with CVSS-adjustment and public-sector weighting | Reproducible cyber-hygiene anomaly benchmark with telemetry-freshness modeling |
| Overlap | None on unit of analysis; both share reproducibility ethos | Paper 3 adds identity / AD / telemetry-freshness dimensions not in Paper 1 |

**Verdict: DISTINCT.** No contribution overlaps. Both use reproducibility as a design principle, but the research problems, datasets, and methods differ.

---

### 5.2 Distinctness from Paper 2

| Dimension | Paper 2 | Paper 3 |
|---|---|---|
| Core topic | Failure-aware calibration gates for vulnerability prioritization under sparse labels | Cyber-hygiene anomaly detection benchmark under stale/missing telemetry |
| Primary task | Calibration / sparse-label sensitivity for vulnerability–host ranking | Unsupervised anomaly detection across identity / endpoint / patch state |
| Calibration role | Primary research question | Not primary; calibration used only where operationally justified and explicitly subordinated to taxonomy + benchmark questions |
| Synthetic data | Vulnerability × host synthetic data (Paper 1 lineage) | New identity–endpoint–patch–vulnerability telemetry schema (no overlap) |
| Failure-aware reporting | Primary methodological contribution | Secondary discipline (C7); methodology adapted for hygiene domain, not duplicated |
| Methods | Calibration metrics, reliability diagrams, gate sensitivity analysis | Isolation Forest, LOF, OCSVM, autoencoder, temporal z-score, graph anomaly detection |

**Verdict: DISTINCT.** Paper 2 focuses on calibration quality for an existing prioritization task. Paper 3 focuses on detecting hygiene anomalies in a new multi-domain schema. The failure-aware reporting principle is shared but applied to a different task and data structure.

**Protective clause:** Paper 3 must not use the same synthetic dataset as Paper 1 or Paper 2. The schema defined in `SCHEMA_v0_1.md` is structurally new.

---

## 6. Feasibility Conclusion

| Dimension | Assessment |
|---|---|
| Fully synthetic generation | **Feasible.** All schema domains are synthetic and seeded. |
| Structural priors | **Partially available.** NVD (CVE severity), DBIR 2026 (patch lag aggregate), CISA BOD 23-01 (telemetry cadence). AD group statistics unavailable — managed via disclosed assumptions and sensitivity sweeps. |
| No employer/production data | **Confirmed.** |
| Schema completeness | **Adequate for v0.1.** Full spec in `SCHEMA_v0_1.md`. |
| Realism challenge | **Manageable.** Sensitivity sweeps over generative parameters; explicit disclosure of assumptions; benchmark-relative performance claims only. |
| Distinctness from Paper 1/2 | **Confirmed.** No unit-of-analysis, schema, or primary-contribution overlap. |

**Overall dataset feasibility: GO.**

---

*End of Step 2 Dataset Feasibility Report.*
