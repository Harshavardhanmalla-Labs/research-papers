# Paper 3 — Step 1: Research Validation Report & Go/No-Go Assessment

**Working title (provisional):**
"ML for Cyber Hygiene: Anomaly Detection Across Active Directory, Endpoint, and Patch Telemetry for Public-Sector Security Operations"

**Author note:** Step 1 is a validation pass only. No code, no experiments, no employer data, no real government data. All citation placeholders are marked `[VERIFY]`. This document determines whether the topic is publishable and EB1A-defensible, and whether it is sufficiently distinct from Paper 1 and Paper 2.

---

## 1. Improved Title Options

The working title is acceptable but slightly over-broad ("for Public-Sector Security Operations" implies deployment context). The following 10 alternatives narrow scope toward a reproducible benchmark and synthetic telemetry, which is what the paper can defensibly claim.

1. **A Reproducible Synthetic Benchmark for Cyber-Hygiene Anomaly Detection Across Identity, Endpoint, and Patch Telemetry**
2. **Cyber-Hygiene Anomaly Detection Under Stale and Missing Telemetry: A Synthetic Identity–Endpoint Benchmark**
3. **HygieneBench: A Reproducible Benchmark for Identity, Endpoint, and Vulnerability Hygiene Anomalies**
4. **Identity–Endpoint Correlation for Cyber-Hygiene Risk Scoring: A Synthetic-Telemetry Benchmark Study**
5. **Anomaly Detection for Active Directory and Endpoint Hygiene Under Telemetry Freshness Constraints**
6. **Evaluating Unsupervised Anomaly Detectors for Cyber-Hygiene Signals Under Class Imbalance and Missingness**
7. **A Synthetic Telemetry Generator and Benchmark Tasks for Identity-Endpoint-Patch Hygiene Anomalies**
8. **Cyber-Hygiene Risk Signals Across Identity and Endpoint State: A Reproducible Evaluation Framework**
9. **Graph-Informed Anomaly Detection for Identity–Endpoint–Vulnerability Hygiene: A Benchmark Study on Synthetic Telemetry**
10. **Toward Reproducible Cyber-Hygiene Anomaly Benchmarks: Methods, Tasks, and Failure Modes on Synthetic AD/Endpoint/Patch Data**

**Recommended title (for Step 2 planning):** Option **1** as primary, Option **3** if a short, brandable name (HygieneBench) is desired.

---

## 2. Research Problem

**Stated precisely:**

> *Can anomaly-detection methods for cyber-hygiene risk signals — spanning identity state (Active Directory), endpoint patch posture, vulnerability exposure, and telemetry freshness — be evaluated in a reproducible way under realistic constraints of class imbalance, label sparsity, missing data, and stale telemetry?*

**What the paper is NOT claiming:**

- It is not claiming to "detect cyberattacks."
- It is not claiming to detect adversarial behavior in real environments.
- It is not claiming superiority over commercial SIEM/UEBA/EDR products.
- It is not claiming a production-deployed system.
- It is not claiming attack-attribution or threat-actor inference.

**What the paper IS claiming:**

- A reproducible, synthetic-telemetry **benchmark** for cyber-hygiene anomaly detection.
- An **anomaly taxonomy** correlating identity, endpoint, patch, and vulnerability state.
- An **evaluation protocol** under stale/missing telemetry and severe class imbalance.
- A **comparison of unsupervised detectors and a rule-based baseline**, including negative results (failure-aware reporting) where models do not outperform rules.

---

## 3. Why the Problem Matters

Operational importance across stakeholders:

- **Public-sector security operations:** SOCs in resource-constrained agencies often run with fragmented telemetry — AD, EDR, vulnerability scanner, patch management, asset inventory — managed by different teams. The hygiene picture across these silos is *the* operational surface that auditors, OIGs, and CISA assessments routinely flag, not novel attack techniques.
- **Identity hygiene:** Stale privileged accounts, dormant accounts reactivated, abnormal group membership drift, and improper privilege escalation paths are recurring findings in federal cyber audits and remain primary precursors to AD-based compromise (e.g., MITRE ATT&CK T1078, T1098).
- **Endpoint remediation:** Patch non-compliance clusters, missing/stale endpoint agents, and unmanaged assets are the dominant operational risk surface and the most common audit findings.
- **Vulnerability management:** Vulnerabilities matter only as a function of which assets/identities are exposed; correlating CVEs with identity state and patch posture is operationally important but largely tool-fragmented.
- **Audit & compliance evidence:** FISMA, NIST 800-53, CISA BOD/ED directives require auditable evidence of hygiene posture; reproducible benchmarks for hygiene-anomaly methods support that evidence chain.
- **Resource-constrained SOC/infrastructure teams:** They cannot deploy heavy ML stacks. A reproducible benchmark establishing whether simple rules suffice — or where ML adds defensible value — is *useful negative or positive evidence* either way.

The motivation is **hygiene and exposure**, not intrusion detection. This framing avoids the crowded UEBA/SIEM space.

---

## 4. Research Gap

**The naive gap ("ML anomaly detection for AD") is too generic.** UEBA vendors, Microsoft Defender for Identity, Entra ID Protection, Splunk UBA, Exabeam, and numerous academic papers already occupy this space. That framing will not survive peer review and will not carry EB1A weight.

**Sharper candidate gaps:**

**Gap A — Reproducibility and benchmarking gap [CANDIDATE].** Despite extensive UEBA and AD-attack-detection literature, there is no open, reproducible benchmark that *jointly* covers identity state, endpoint patch posture, vulnerability exposure, and telemetry freshness/missingness, with documented anomaly injection, fixed splits, and audit artifacts. Existing public datasets (LANL, CERT insider threat, CICIDS, DARPA, Mordor) [VERIFY] cover *attack* or *user-activity* signals, not cyber-hygiene state.

**Gap B — Hygiene framing rather than attack framing [CANDIDATE].** Most academic AD/UEBA work targets adversary behavior. Cyber hygiene — stale identities, drifted group memberships, patch non-compliance, telemetry staleness — is operationally dominant but under-formalized as a benchmark task family.

**Gap C — Telemetry-freshness and missingness modeling [CANDIDATE].** Operational SOC reality is missing/stale signals. Most ML evaluations assume clean, complete telemetry. There is little benchmarking work that systematically varies telemetry staleness, agent missingness, and inventory mismatch as first-class evaluation conditions.

**Gap D — Identity–endpoint–vulnerability correlation [CANDIDATE].** Existing tools usually treat AD, EDR, and vulnerability management as separate domains. Joint correlation (a critical asset with a critical vulnerability *and* a stale privileged account) is operationally interesting but rarely formalized in academic benchmarks.

**Strongest surviving gap (combined):**

> An **open, reproducible benchmark for cyber-hygiene anomaly detection** that **jointly correlates identity state, endpoint patch posture, vulnerability exposure, and telemetry freshness** under **public-sector-shaped operational constraints** (class imbalance, sparse labels, missing/stale data), with **failure-aware evaluation** that reports when simple rules already suffice.

**Critical self-check:** Does this gap survive against Mordor/Security Datasets, BOTSv3, the LANL Unified Host & Network Data Set, and federal NCCoE practice guides? Plausibly yes — those resources emphasize attack telemetry or NIST control mapping, not hygiene-anomaly benchmarking with telemetry freshness as a controlled variable. Step 2 must falsify this assumption against specific named resources before the gap is locked.

---

## 5. Adjacent Work and Standards (Citation Categories)

All entries below are placeholders marked `[VERIFY]`. No specific references are invented here; Step 2 will populate them.

| # | Category | Why needed | Status |
|---|---|---|---|
| 1 | Active Directory security & identity hygiene research | Position vs. AD attack/abuse literature | `[VERIFY]` |
| 2 | UEBA / user-behavior analytics academic literature | Show this is not yet-another-UEBA paper | `[VERIFY]` |
| 3 | SIEM anomaly detection (academic and vendor whitepapers) | Differentiate from SIEM correlation rules | `[VERIFY]` |
| 4 | Graph-based anomaly detection (general + cyber-specific) | Justify graph-method baseline | `[VERIFY]` |
| 5 | Endpoint cyber-hygiene / patch management literature | Frame endpoint hygiene side | `[VERIFY]` |
| 6 | Vulnerability prioritization / exposure management research | Distinguish from Paper 1/2 | `[VERIFY]` |
| 7 | MITRE ATT&CK techniques (T1078, T1098, T1003, T1484, T1556 etc.) | Map hygiene anomalies to ATT&CK only where defensible | `[VERIFY]` |
| 8 | CISA guidance (BOD 23-01 asset visibility, BOD 22-01 KEV, identity guidance) | Public-sector operational framing | `[VERIFY]` |
| 9 | NIST standards (800-53, 800-207 zero trust, SP 800-40 patching, CSF 2.0) | Compliance grounding | `[VERIFY]` |
| 10 | Public cyber datasets (LANL, CERT insider threat, CICIDS, DARPA TC, Mordor / Security Datasets, BOTSv3) | Establish reproducibility comparators | `[VERIFY]` |
| 11 | Synthetic data generation for cybersecurity (e.g., adversary emulation, blue-team simulators) | Justify synthetic-only approach | `[VERIFY]` |
| 12 | Class imbalance & anomaly-detection evaluation methodology (PR-AUC, P@k, calibration, rank stability) | Methodological grounding | `[VERIFY]` |
| 13 | Microsoft Defender for Identity / Entra ID Protection / Sentinel — public documentation | Position vs. vendor stack | `[VERIFY]` |
| 14 | Splunk UBA / Exabeam public materials | Position vs. vendor UEBA | `[VERIFY]` |

**Rule:** No specific paper, author, or year is asserted in Step 1. Step 2 will perform a falsification pass and replace `[VERIFY]` with confirmed references.

---

## 6. Prior-Art Threat Assessment

Threat levels: **low / medium / high / fatal.** All entries below are best-effort characterizations and must be confirmed in Step 2.

| Source / tool / dataset | What it does | AD? | Endpoint patch posture? | Vulnerability data? | Telemetry freshness / missingness? | Public / reproducible? | Threat to novelty | Required differentiation |
|---|---|---|---|---|---|---|---|---|
| LANL Unified Host & Network Data Set `[VERIFY]` | Real auth + network events for research | Partial (auth events) | No | No | No | Yes | **Medium** | LANL is attack/auth research; we frame hygiene state & joint identity–endpoint–patch correlation |
| CERT Insider Threat dataset `[VERIFY]` | Synthetic insider-threat behavioral logs | Partial | No | No | No | Yes | Medium | Insider behavior ≠ cyber hygiene; different anomaly taxonomy |
| CICIDS / CSE-CIC-IDS `[VERIFY]` | Network IDS dataset | No | No | No | No | Yes | Low | Network IDS; not hygiene |
| DARPA TC `[VERIFY]` | Provenance / APT detection | Partial | No | No | No | Partial | Low–Medium | APT detection; not hygiene |
| Mordor / Security Datasets project `[VERIFY]` | Attack-emulation telemetry (Sysmon/AD) | Yes | No | No | No | Yes | **High** on AD framing; Low on hygiene | Re-frame to hygiene state and freshness, not attack emulation |
| BOTSv3 (Splunk) `[VERIFY]` | Boss-of-the-SOC dataset | Yes | Partial | Partial | No | Yes | Medium | Attack-investigation framing |
| Microsoft Defender for Identity `[VERIFY]` | Productized AD attack detection | Yes | No | No | No | No (closed) | **High** on AD detection; not a benchmark | We provide an open benchmark, not a product; hygiene not attacks |
| Entra ID Protection `[VERIFY]` | Identity risk scoring (cloud IdP) | Cloud only | No | No | No | No (closed) | Medium | On-prem AD hygiene + endpoint + vuln correlation; open benchmark |
| Splunk UBA / Exabeam `[VERIFY]` | UEBA products | Yes | Partial | Partial | No | No (closed) | High | Not a UEBA replacement; hygiene benchmarking, reproducible |
| Microsoft Sentinel `[VERIFY]` | SIEM | Yes | Yes (connectors) | Partial | Partial | No | High | Not competing with SIEM; producing a research benchmark |
| Graph anomaly detection literature (general) `[VERIFY]` | Methods (e.g., DOMINANT, AnomalyDAE) | N/A | N/A | N/A | N/A | Partial | Medium | We adopt them as baselines; novelty is dataset & joint framing |
| Vulnerability prioritization research (incl. Paper 1) | Rank CVE×asset pairs | No | Partial | Yes | Partial | Mixed | Medium | We focus on hygiene anomalies across identity+endpoint+vuln, not pair-prioritization |
| NIST NCCoE practice guides `[VERIFY]` | Reference architectures (e.g., zero trust, asset mgmt) | Yes | Yes | Yes | Partial | Partial | Low–Medium | Architectural guidance, not a benchmark |
| Microsoft BloodHound / AD attack graph tools `[VERIFY]` | AD attack-path enumeration | Yes | No | No | No | Yes (OSS) | Medium | We use as baseline framing for graph-based hygiene risk, not attack paths |
| Open-source exposure mgmt tools (e.g., Snyk-like, OWASP-related) `[VERIFY]` | Exposure mgmt | No | Partial | Yes | No | Partial | Low | Different domain |

**Highest threats: Mordor/Security Datasets, Microsoft Defender for Identity, Splunk UBA, Sentinel.** None of these is fatal *if* we firmly anchor the contribution to (a) **open synthetic benchmark**, (b) **hygiene-anomaly taxonomy**, (c) **telemetry-freshness as a controlled evaluation variable**, and (d) **joint identity–endpoint–vulnerability correlation**.

**Biggest single novelty threat:** The **Mordor / Security Datasets** project [VERIFY], because it already provides reproducible AD-related telemetry. Differentiation must be unambiguous: hygiene state (not attacks), patch + vulnerability joint state (not endpoint events alone), and freshness/missingness as first-class variables.

---

## 7. Proposed Original Contribution (Candidates)

The following 7 candidates form the contribution menu. Step 2 will select 3–5.

1. **Synthetic identity–endpoint–patch–vulnerability cyber-hygiene telemetry generator.** Configurable population sizes, group structures, patch cycles, vulnerability injection, telemetry-freshness models, and missingness regimes. Deterministic seeds; documented schema.
2. **Cyber-hygiene anomaly taxonomy.** A formal taxonomy linking AD state, endpoint posture, patch state, vulnerability exposure, and telemetry freshness; each class defined operationally and mapped to MITRE ATT&CK *only where defensible* (e.g., stale privileged account ↔ T1078.002 `[VERIFY]`).
3. **Benchmark task suite under stale/missing telemetry.** Tasks parameterized over class imbalance, label sparsity, freshness decay, agent missingness, and inventory mismatch.
4. **Comparative evaluation of unsupervised anomaly detectors.** Rule baseline, Isolation Forest, LOF, One-Class SVM, autoencoder, simple temporal z-score, and a graph-based detector; precision@k / recall@k / AP, rank stability, false-positive burden, time-to-detection.
5. **Joint identity–endpoint–vulnerability risk scoring (hybrid).** A reproducible hybrid scorer combining identity state + endpoint posture + vulnerability exposure features; evaluated *as a baseline*, not claimed as deployment-ready.
6. **Reproducibility & audit pipeline.** Frozen seeds, dataset cards, model cards, run manifests, deterministic splits, and an inspection/reporting layer (consistent with Paper 1 reproducibility ethos).
7. **Failure-aware (negative-result) reporting.** Explicit reporting of conditions where ML *does not* outperform simple rules — calibrated to public-sector SOC reality where false-positive burden dominates utility.

---

## 8. Data Feasibility

**Constraint:** No employer logs. No ADOT data. No real account names. No production architecture. No live security events. No sensitive indicators.

**Options:**

| Option | Description | Feasibility | Risk |
|---|---|---|---|
| A | Fully synthetic telemetry only | **High** — full control, no privacy risk, deterministic | Realism rebuttal: "is your synthetic AD plausible?" → address via schema fidelity + documented assumptions |
| B | Public datasets only | Medium — public AD/endpoint/vuln joint datasets are rare; mostly attack-focused | Mismatch with hygiene framing |
| C | Hybrid synthetic + public structural priors | Medium–High — borrow structural distributions (e.g., AD group sizes, patch lag distributions) from published statistics `[VERIFY]` | Citation & assumption hygiene must be tight |
| D | Employer data | **Forbidden** | N/A |

**Recommendation: Option A primary, Option C secondary** — fully synthetic data with structural priors drawn from *published, public* statistics (cited, marked `[VERIFY]` until confirmed in Step 2). No real telemetry.

**Candidate schema (draft, to refine in Step 2):**

- **Entities:** `users`, `groups`, `computers`, `assets`, `applications`
- **Identity events:** `login_events`, `logon_failures`, `privileged_role_changes`, `group_membership_events`, `account_lifecycle_events` (create / disable / reactivate / password reset)
- **Endpoint state:** `endpoint_patch_state` (per-asset patch level, cycle), `endpoint_agent_state` (agent installed / heartbeat freshness), `endpoint_config_drift`
- **Vulnerability state:** `vulnerability_records` (CVE × asset, with severity, KEV flag, age)
- **Asset metadata:** `asset_criticality`, `asset_owner_org`, `network_segment`
- **Telemetry meta:** `last_seen_per_source`, `telemetry_freshness`, `source_missingness_indicator`
- **Remediation:** `remediation_events` (action, latency, outcome)
- **Labels:** `anomaly_labels` (per anomaly class, with severity & ground-truth provenance)

All synthetic, all seeded, all documented.

---

## 9. Evaluation Design

**Benchmark tasks (initial menu):**

1. **T1 — Stale privileged account risk.** Inject accounts in privileged groups that have not logged in for N days; detect.
2. **T2 — Group membership drift.** Inject anomalous group additions deviating from a baseline group-composition distribution; detect.
3. **T3 — Endpoint–identity risk correlation.** Inject co-occurrence of high-criticality endpoint + stale agent + privileged user + open critical vuln; detect.
4. **T4 — Telemetry missingness clusters.** Inject systematic source-missingness (e.g., a whole OU loses EDR telemetry); detect.
5. **T5 — Patch/vulnerability hygiene anomalies.** Inject patch-noncompliance clusters and KEV-flagged exposures aging past threshold; detect.
6. **T6 — Dormant account reactivation.** Inject reactivation events with abnormal post-reactivation behavior; detect.
7. **T7 — Privilege escalation drift.** Inject gradual privilege escalation patterns across multiple days; detect.

**Metrics (per task):**

- **Precision@k**, **Recall@k** (with k mapped to realistic SOC daily/weekly review budget).
- **Average precision (AP)** — preferred over ROC-AUC under heavy imbalance.
- **ROC-AUC** — reported only when class balance permits; otherwise omitted.
- **False-positive burden** (FPs per N alerts, mapped to analyst-review cost).
- **Time-to-detection** (event injection time → first detection rank position).
- **Rank stability** under seed and split perturbation.
- **Reproducibility / auditability** metrics: manifest completeness, seed reproducibility, dataset-card completeness, run determinism.

**Calibration:** Not required globally. Required only on tasks where a thresholded operational decision is simulated — and reported only with explicit justification. (Avoids overlap with Paper 2's calibration-gates focus.)

**Conditions / sweeps:**

- Telemetry freshness decay (none / mild / heavy)
- Source missingness (none / one source / two sources)
- Class imbalance ratios
- Label sparsity (fully labeled vs. partially labeled vs. unlabeled)
- Population scale (small / medium / large)

**Negative-result protocol:** For each task and condition, report whether ML detectors statistically beat the rule baseline. Where they do not, report it. This is a contribution, not a failure.

---

## 10. Risks of Overclaiming — Forbidden Claims

The following claims are **forbidden** in this paper:

- "Detects real cyberattacks."
- "Validated in production."
- "Deployed at a government agency / Department of Transportation / ADOT."
- "Superior to SIEM, EDR, or UEBA products."
- "Achieves compliance" / "compliant with NIST/FISMA/CISA directive X."
- "Replaces security analysts."
- "Built on real AD / employer / agency data."
- "Proves attacker behavior" / "identifies threat actors."
- "Generalizes to all government environments."
- "Suitable for production SOC deployment."

**Allowed framing:** reproducible benchmark, synthetic telemetry, evaluated under controlled conditions, *with explicit caveats about synthetic-data realism limits*.

---

## 11. Confidentiality Risks

Explicit confirmations:

- **No employer logs** used at any stage.
- **No ADOT data** used at any stage.
- **No real user / account / device / asset names** in any artifact.
- **No internal control narratives**, audit findings, or policy text reproduced.
- **No production architecture diagrams** (employer, ADOT, or otherwise).
- **No live security events** referenced or analyzed.
- **No sensitive indicators** (IOCs tied to real incidents, internal IPs, etc.).

All data is synthetic. All examples in the paper are synthetic. The synthetic generator's parameters are seeded and disclosed.

---

## 12. Feasibility Scoring

Brutally honest. Scale 1–10; for the "risk" row, **higher = more risk** (i.e., worse).

| Dimension | Score | Justification |
|---|---|---|
| **Novelty** | **6 / 10** | Hygiene-benchmark framing + telemetry-freshness as first-class variable is defensible. But AD anomaly detection broadly is *crowded*. Novelty depends on locking the gap to *benchmark + hygiene + freshness + joint correlation*, not "ML on AD." |
| **Publishability** | **7 / 10** | Workshop or industry-track venues are realistic (e.g., ACSAC industry, USENIX security workshops, IEEE BigData / SecML workshops `[VERIFY]`). Top-tier acceptance is plausible only with strong reproducibility and a credible synthetic generator. |
| **EB1A value** | **6.5 / 10** | Strong if positioned as an *open, reproducible public-sector-oriented benchmark* with adoption pathway (GitHub release, dataset card, reproducibility kit). Weak if positioned as "yet another anomaly detector." Distinct enough from Paper 1 and Paper 2 to count as a separate contribution. |
| **Implementation complexity** | **7 / 10** | Synthetic AD/endpoint/patch/vuln telemetry generator is non-trivial; graph baselines add complexity. Manageable in a single-author timeline if scope is fixed at Step 2. |
| **Data feasibility** | **8 / 10** | Fully synthetic + public structural priors is achievable. Realism rebuttal is the main risk, addressable via documented assumptions and sensitivity sweeps. |
| **Risk (higher = worse)** | **5 / 10** | Main risks: (a) prior-art collision with Mordor/Defender/UBA framings, (b) reviewers questioning synthetic-realism, (c) overlap with Paper 1's reproducibility framing. All manageable with tight scoping. |

**Overall:** Publishable and EB1A-relevant if and only if the gap is narrowed and Mordor/Defender/UBA differentiation is explicit.

---

## 13. Recommended Decision

# **CONDITIONAL GO**

**Conditions to satisfy before committing to a full Paper 3 effort:**

1. **Falsify the gap against Mordor / Security Datasets, LANL, CERT, BOTSv3, and Defender for Identity** in Step 2. If any of these already provides the benchmark contributions in §7.1–§7.3, pivot.
2. **Lock the contribution menu to 3–5 items** from §7, with at least one being the synthetic generator and at least one being the failure-aware evaluation.
3. **Confirm structural priors are publicly citable** (e.g., AD group-size statistics, patch-lag distributions). If not, narrow synthetic-realism claims.
4. **Confirm distinctness from Paper 2** by requiring Paper 3 *not* to lead with calibration; Paper 3 leads with *anomaly taxonomy + benchmark*, and uses calibration only where operationally justified.
5. **Confirm distinctness from Paper 1** by ensuring Paper 3's unit of analysis is the *entity-state record across identity/endpoint/patch* — not the vulnerability×host *pair*.

**Recommendation:** Proceed to **Step 2 — Prior-Art Falsification & Dataset Feasibility.** Do not yet start drafting, coding, or experiment design.

---

## 14. Recommended Final Outline (If Pursued) — 16 Sections

Outline only. Do not draft.

1. **Abstract**
2. **Introduction** — hygiene framing, public-sector context, what this paper is *not*.
3. **Background and Related Work** — AD security, UEBA, SIEM anomaly detection, graph anomaly detection, endpoint hygiene, vulnerability management, public cyber datasets.
4. **Problem Definition** — cyber-hygiene anomaly detection across identity, endpoint, patch, vulnerability telemetry, under freshness/missingness.
5. **Cyber-Hygiene Anomaly Taxonomy** — formal definitions, operational mapping, MITRE ATT&CK references where defensible.
6. **Synthetic Telemetry Generator** — schema, generative model, structural priors, parameters, seeds.
7. **Benchmark Tasks** — T1–T7, formal task definitions, evaluation budgets.
8. **Methods** — rule baseline, Isolation Forest, LOF, One-Class SVM, autoencoder, temporal z-score, graph anomaly detector, hybrid risk score.
9. **Evaluation Protocol** — metrics, splits, sweeps, reproducibility & audit metrics.
10. **Results** — per task, per condition, with failure-aware reporting.
11. **Ablations and Sensitivity** — freshness decay, missingness, class imbalance, label sparsity, population scale.
12. **Reproducibility and Auditability** — manifests, seeds, dataset/model cards, run determinism.
13. **Discussion** — when ML helps, when rules suffice; limits of synthetic data; operational implications.
14. **Threats to Validity** — synthetic realism, taxonomy coverage, generalization claims.
15. **Ethical and Confidentiality Considerations** — no real data, dual-use considerations, responsible disclosure not applicable.
16. **Conclusion and Future Work** — explicit non-claims, future-work pointers (real-data validation as future work, *not* part of this paper).

---

## 15. Isolation Check

- **`paper3/` created as a sibling tree** at `/Users/sowmyasreeogiboyina/Research Papers/paper3/`. Subdirectories: `manuscript/`, `design/`, `feasibility/`, `references/`, `decision_logs/`.
- **Paper 1 untouched.** No files created or modified under `paper1-vuln-prioritization/paper/`, `paper1-vuln-prioritization/results/`, or `paper1-vuln-prioritization/src/paper1/`.
- **Paper 2 untouched.** No files created or modified under `paper1-vuln-prioritization/paper2/`, `paper1-vuln-prioritization/paper2/results/`, `paper1-vuln-prioritization/paper2/audit/`, or `paper1-vuln-prioritization/paper2_runtime/`.
- **No experiments run.**
- **No code written.**
- **No employer or production data referenced.**
- **No citations fabricated.** All references marked `[VERIFY]` and pending Step 2 falsification.

---

*End of Step 1 — Research Validation Report.*
