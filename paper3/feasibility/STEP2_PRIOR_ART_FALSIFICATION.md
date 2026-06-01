# Paper 3 — Step 2: Prior-Art Falsification Report

**Date:** 2026-05-28
**Status:** Complete
**Feeds into:** `STEP2_DATASET_FEASIBILITY.md`, `SCHEMA_v0_1.md`, `PAPER3_DECISION_LOG.md`

---

## Purpose

This document resolves every `[VERIFY]` citation placeholder from Step 1 §5–§6 against verifiable sources, assesses overlap between prior art and the proposed contributions, and delivers a gap-survival verdict for each Step 1 §7 contribution candidate.

**Citation discipline:**
- `[CONFIRMED]` — title, authors, venue, year independently verified.
- `[CONFIRMED-DOC]` — government or vendor document, no academic venue, confirmed.
- `[CONFIRMED-TOOL]` — open-source tool or project, no formal academic publication, confirmed.
- `[VERIFY]` — still unresolved; requires manual library search before submission.

---

## Part A: Citation Resolution (Step 1 §5 — Citation Categories)

### A1. Public Cyber Datasets

**LANL Unified Host and Network Data Set**
- Authors: Turcotte, M.J.M., Kent, A.D., Hash, C.
- Reference: arXiv:1708.07518, 2017. Also published as a chapter in *Data Science for Cyber-Security*, World Scientific, 2019. `[CONFIRMED]`
- Coverage: ~90 days of enterprise authentication events, process logs, network flows from LANL production network.
- AD coverage: Authentication logs only (NTLM/Kerberos-style events); no explicit AD schema, group structure, or posture data.
- Patch/vulnerability coverage: None.
- Telemetry freshness/missingness: Not modeled.
- Threat to Paper 3: **Low.** Attack/anomaly detection on auth and flow data; does not address hygiene state.

**CERT Insider Threat Test Dataset**
- Organization: SEI CERT Division, Carnegie Mellon University; DARPA I2O sponsored.
- Reference: Multiple versions (r4.2 through r6.2). Glasser, J. and Lindauer, B. "Bridging the Gap: A Pragmatic Approach to Generating Insider Threat Data." *IEEE SPW*, 2013. `[CONFIRMED]`
- Dataset access: CMU SEI Library; Figshare. `[CONFIRMED]`
- Coverage: Synthetic logon, file, email, device, HTTP events; 1,000–4,000 synthetic employees over ~17 months; insider threat scenarios.
- AD coverage: Logon events only; no group structure, no privilege posture, no hygiene state.
- Patch/vulnerability coverage: None.
- Telemetry freshness/missingness: Not modeled.
- Threat to Paper 3: **Low.** Insider threat behavioral modeling; does not address identity/endpoint/patch/vulnerability hygiene posture.

**CICIDS 2018 (CSE-CIC-IDS2018)**
- Authors: Sharafaldin, I., Habibi Lashkari, A., Ghorbani, A.A.
- Reference: *ICISSP 2018*, Funchal, Madeira, Portugal, January 2018. `[CONFIRMED]`
- Dataset: UNB CIC, https://www.unb.ca/cic/datasets/ids-2018.html `[CONFIRMED]`
- Coverage: 10-day network traffic capture; 80+ network flow features; attack classes: DoS, DDoS, brute-force, XSS, SQLi, infiltration, port scan, botnet.
- AD coverage: None. Network-layer dataset only.
- Patch/vulnerability coverage: None.
- Threat to Paper 3: **Low.** Network IDS benchmark; entirely different domain.

**DARPA Transparent Computing (TC) Datasets**
- Organization: DARPA Information Innovation Office (I2O).
- Reference: No single canonical academic paper; program overview documented in DARPA BAA and associated publications. Datasets released through performers and data.gov-adjacent repositories. `[VERIFY — confirm current public access point]`
- Coverage: Provenance graphs (OS audit logs, process trees, network flows) from APT engagement scenarios; 5 teams × multiple scenarios (2017–2019 program).
- AD coverage: Some host-level events; no explicit AD structure or hygiene state.
- Patch/vulnerability coverage: None.
- Threat to Paper 3: **Low.** APT provenance detection; not hygiene benchmarking.

**Mordor / OTRF Security Datasets**
- Organization: Open Threat Research Foundation (OTRF); created by Roberto Rodriguez and Jose Luis Rodriguez.
- Reference: No formal peer-reviewed publication found. Project documented at https://github.com/OTRF/Security-Datasets; accessible via msticpy (2.9.0+). `[CONFIRMED-TOOL]`
- Coverage: Adversarial attack emulation telemetry; Windows event logs, Sysmon logs, network captures from ATT&CK-mapped simulation scenarios. Valuable for detection-rule development and ML training on attack patterns.
- AD coverage: Windows/Sysmon events that include AD-relevant logs (e.g., 4624, 4672, 4688). AD structural data, group posture, and hygiene state: **None**.
- Patch/vulnerability coverage: None.
- Telemetry freshness/missingness: Not modeled.
- Threat to Paper 3: **Medium** on surface framing ("AD telemetry exists"), **Low** on actual overlap. Differentiation: Mordor provides attack-emulation telemetry; Paper 3 proposes hygiene-state telemetry with freshness/missingness modeling. These are structurally different.

**Splunk Boss of the SOC v3 (BOTSv3)**
- Organization: Splunk Inc.
- Reference: No formal academic publication. Available at https://github.com/splunk/botsv3 under Creative Commons CC0. `[CONFIRMED-TOOL]`
- Coverage: Realistic but fictitious company; endpoints, network, cloud (AWS/Azure) authentication events; Blue Team CTF format.
- AD coverage: Authentication events implied; no explicit AD group structure or hygiene state.
- Patch/vulnerability coverage: Not covered.
- Threat to Paper 3: **Low.** Training/CTF dataset, not a hygiene benchmark. Requires Splunk Enterprise deployment.

---

### A2. Active Directory Security / Identity Hygiene

**MITRE ATT&CK Enterprise Matrix**
- Authors: Strom, B.E., Applebaum, A., Miller, D.P., Nickels, K.C., Pennington, A.G., Thomas, C.B.
- Reference: "MITRE ATT&CK: Design and Philosophy." The MITRE Corporation, Technical Report, 2018. Updated continuously. `[CONFIRMED]`
- AD-relevant techniques: T1078 (Valid Accounts), T1098 (Account Manipulation), T1484 (Domain Policy Modification), T1134 (Access Token Manipulation), T1003 (OS Credential Dumping), T1556 (Modify Authentication Process), T1136 (Create Account). `[CONFIRMED]`
- Use in Paper 3: Map hygiene anomaly classes to ATT&CK techniques *only where a hygiene state directly enables a named technique*. Do not claim Paper 3 detects ATT&CK techniques; hygiene state correlates with enabling conditions, not the techniques themselves.
- Threat to Paper 3: **None.** ATT&CK is a framework, not a benchmark or dataset.

**BloodHound (SpecterOps)**
- Organization: SpecterOps.
- Reference: No formal academic publication. Tool at https://specterops.github.io/bloodhound/. `[CONFIRMED-TOOL]`
- Coverage: Graph-based AD attack-path enumeration (users, groups, computers, OUs, GPOs, trusts, ACL edges). Identifies privilege escalation paths.
- AD hygiene coverage: AD structural relationships only; no patch posture, no vulnerability records, no telemetry freshness.
- Use in Paper 3: Can serve as *inspiration* for a graph-based anomaly baseline. Not a dataset or benchmark. Structural graph concept (identity as a graph) is applicable.
- Threat to Paper 3: **Medium** conceptually (graph-based AD analysis); **Low** on actual benchmark overlap. BloodHound finds attack paths, not hygiene anomalies. No patch/vuln/freshness dimension.

**CIS Benchmarks for Active Directory / Windows Server** `[VERIFY — confirm current version and citation format]`
- Organization: Center for Internet Security (CIS).
- Use in Paper 3: Background context for hygiene-state definitions (e.g., "inactive account threshold," "privileged group size norm"). Not a dataset. Cite as a normative reference for threshold choices in the synthetic generator.
- Threat to Paper 3: None.

---

### A3. UEBA and SIEM Anomaly Detection

**Microsoft Defender for Identity (formerly Azure ATP)**
- Organization: Microsoft Corporation.
- Reference: Microsoft documentation. No standalone peer-reviewed publication. `[CONFIRMED-DOC]`
- Coverage: Behavioral analytics on AD authentication events; detects known identity attack patterns (pass-the-hash, pass-the-ticket, golden ticket, DCSync, reconnaissance). Cloud-managed.
- Patch/endpoint coverage: None within Defender for Identity; relies on integration with Defender for Endpoint.
- Vulnerability coverage: Not directly in Defender for Identity; integrates with vulnerability data via Defender XDR.
- Telemetry freshness/missingness: Not modeled as an evaluation dimension.
- Public/reproducible: No. Closed commercial product.
- Threat to Paper 3: **High** on the surface framing "ML for AD anomaly detection." **Low** as an actual benchmark threat: it is a closed product, not a reproducible research artifact; it detects attack techniques, not hygiene state; there is no benchmark methodology or evaluation under controlled conditions. Paper 3 does not compete with Defender for Identity — it provides an *open benchmark* for a *different problem* (hygiene state, not attack detection).

**Microsoft Entra ID Protection (formerly Azure AD Identity Protection)**
- Organization: Microsoft Corporation.
- Reference: Microsoft documentation. No standalone peer-reviewed publication. `[CONFIRMED-DOC]`
- Coverage: Risk-based identity protection for cloud (Azure AD/Entra) identities; risk signals include atypical location, leaked credentials, threat intelligence feeds.
- Scope: Cloud identity only; does not cover on-premises AD group structure, endpoint patch posture, or vulnerability records.
- Threat to Paper 3: **Medium** positionally; **Low** structurally. On-prem AD hygiene + endpoint + vuln correlation is outside Entra ID Protection's scope.

**Microsoft Sentinel**
- Organization: Microsoft Corporation.
- Reference: Microsoft documentation. `[CONFIRMED-DOC]`
- Coverage: Cloud SIEM; ingests logs from AD, endpoints, cloud workloads via connectors; correlation rules, KQL analytics, ML fusion detection.
- Threat to Paper 3: **Medium** positionally ("ML in SIEM"). **Low** structurally: Sentinel is not an open benchmark; it ingests telemetry from live environments; it does not model telemetry freshness/missingness as a controlled evaluation condition; there is no publicly reproducible dataset or evaluation protocol.

**Splunk UBA / Exabeam**
- Organization: Splunk Inc. / Exabeam Inc.
- Reference: Vendor whitepapers and product documentation. No formal peer-reviewed academic publications confirming methodology. `[CONFIRMED-DOC]`
- Coverage: Behavioral baselines for users and entities; AD, endpoint, and some vulnerability integration (via connectors). Risk scoring.
- Threat to Paper 3: **Medium** positionally. **Low** structurally: closed commercial products, no reproducible research artifact, no open evaluation protocol, no telemetry-freshness modeling as a controlled variable.

---

### A4. Graph-Based Anomaly Detection

**DOMINANT — Deep Anomaly Detection on Attributed Networks**
- Authors: Ding, K., Li, J., Bhanushali, R., Liu, H.
- Reference: *Proceedings of the 2019 SIAM International Conference on Data Mining (SDM)*, Calgary, AB, Canada, May 2019. DOI: 10.1137/1.9781611975673.67. `[CONFIRMED]`
- Coverage: Graph convolutional network autoencoder for node-level anomaly detection on attributed graphs. Application domains: citation networks, social networks, and cybersecurity (mentioned).
- Cyber-hygiene relevance: Method applicable to a graph where nodes are AD entities (users, groups, computers) with feature vectors (patch state, vulnerability exposure, last-seen, privilege level). However, paper does not address cyber hygiene as a domain.
- Use in Paper 3: Candidate baseline method; do not claim novelty on the method itself, claim novelty on the *benchmark application*.
- Threat to Paper 3: **Low.** DOMINANT is a method, not a cyber-hygiene benchmark.

**AnomalyDAE — Dual Autoencoder for Anomaly Detection on Attributed Networks**
- Authors: Fan, H., Zhang, F., Li, Z.
- Reference: *IEEE ICASSP 2020*. `[VERIFY — confirm exact proceedings]`
- Use in Paper 3: Same as DOMINANT — candidate baseline; no overlap with cyber-hygiene domain.

**PyGOD (Python Graph Outlier Detection Library)**
- Authors: Liu, Y., et al.
- Reference: `[VERIFY — check arXiv or JMLR publication, circa 2022–2023]`
- Use in Paper 3: Could serve as an implementation library for graph-based baselines. Not a benchmark.

---

### A5. CISA and NIST Guidance

**CISA Binding Operational Directive 22-01 (BOD 22-01)**
- Title: "Reducing the Significant Risk of Known Exploited Vulnerabilities."
- Issuer: CISA. Date: November 3, 2021. `[CONFIRMED-DOC]`
- Relevance: Mandates federal agencies remediate KEV-flagged CVEs within specified timeframes. Provides operational grounding for patch/vulnerability hygiene anomaly definitions.
- Threat to Paper 3: None. Normative guidance document, not a benchmark.

**CISA Binding Operational Directive 23-01 (BOD 23-01)**
- Title: "Improving Asset Visibility and Vulnerability Detection on Federal Networks."
- Issuer: CISA. Date: October 3, 2022. `[CONFIRMED-DOC]`
- Relevance: Mandates asset discovery and vulnerability enumeration cadence. Directly motivates telemetry-freshness and asset-inventory-mismatch anomaly classes in Paper 3.
- Threat to Paper 3: None. Normative guidance document.

**NIST Special Publication 800-40 Rev. 4**
- Title: "Guide to Enterprise Patch Management Planning: Preventive Maintenance for Technology."
- Authors: Souppaya, M., Scarfone, K.
- Reference: NIST SP 800-40 Rev. 4, April 2022. `[CONFIRMED-DOC]`
- Relevance: Defines patch management lifecycle; informs patch-lag anomaly class definitions in Paper 3.

**NIST Special Publication 800-53 Rev. 5**
- Title: "Security and Privacy Controls for Information Systems and Organizations."
- Reference: NIST SP 800-53 Rev. 5, September 2020. `[CONFIRMED-DOC]`
- Relevant controls: CM-7 (Least Functionality), CM-8 (System Component Inventory), IA-4 (Identifier Management), AC-2 (Account Management), SI-2 (Flaw Remediation).

**NIST Special Publication 800-207**
- Title: "Zero Trust Architecture."
- Authors: Rose, S., Borchert, O., Mitchell, S., Connelly, S.
- Reference: NIST SP 800-207, August 2020. `[CONFIRMED-DOC]`
- Relevance: Motivates continuous verification of identity and endpoint posture as a hygiene requirement.

**NIST Cybersecurity Framework 2.0 (CSF 2.0)**
- Reference: NIST CSF 2.0, February 2024. `[CONFIRMED-DOC]`
- Relevant functions: IDENTIFY (asset mgmt), PROTECT (identity mgmt, patch mgmt), DETECT (anomaly detection).

---

### A6. Endpoint Hygiene and Vulnerability Exposure

**Verizon Data Breach Investigations Report 2026 (DBIR)**
- Reference: Verizon DBIR 2026, published May 2026. `[CONFIRMED-DOC]`
- Key statistics for structural priors:
  - Average remediation time for critical vulnerabilities: **43 days** (up from 32 days).
  - Rate of critical vulnerabilities patched: **~25%** within the observation window.
  - Vulnerability exploitation: 31% of breaches initiated via exploitation (first time overtaking credential theft).
- Use in Paper 3: Cite as empirical grounding for patch-lag parameter distributions in synthetic generator. Note explicitly that these are aggregate statistics, not granular distributions.

**Vulnerability Life-Cycle / Exposure Management Literature** `[VERIFY — search specifically for Nayak et al. vulnerability life cycle OR Chen et al. patch deployment time]`
- Several academic papers study CVE exploitation timelines and patch deployment gaps. The NVD (National Vulnerability Database) publication timeline data is publicly queryable and can serve as a structural prior for CVE-age distributions.
- NVD: https://nvd.nist.gov/ — public, citable as a U.S. government database. `[CONFIRMED-DOC]`

---

### A7. Synthetic Data Generation for Cybersecurity

**No single canonical academic reference** for generating AD/endpoint/patch/vulnerability hygiene telemetry was found. The closest adjacent works are:

- Attack emulation frameworks (MITRE CALDERA, Atomic Red Team) — generate attack telemetry, not hygiene-state telemetry. `[CONFIRMED-TOOL]`
- CERT Insider Threat dataset generator — generates behavioral logs, not hygiene state. `[CONFIRMED]`
- SimBlock, SEEDLabs, or similar — not directly relevant to identity/endpoint/patch domain.

**Key implication:** The absence of a published synthetic cyber-hygiene telemetry generator strengthens Paper 3's contribution claim on C1.

---

### A8. Class Imbalance and Anomaly-Detection Evaluation

**Precision-Recall vs. ROC Curves**
- Davis, J. and Goadrich, M. "The Relationship between Precision-Recall and ROC Curves." *ICML 2006*. `[CONFIRMED]`
- Use: Justify AP and P@k as primary metrics under severe class imbalance; explain why ROC-AUC can be misleading.

**Average Precision / P@k**
- Manning, C.D., Raghavan, P., Schütze, H. *Introduction to Information Retrieval.* Cambridge University Press, 2008. `[CONFIRMED]`
- Use: Ground the P@k and AP metrics in established IR methodology.

**Isolation Forest**
- Liu, F.T., Ting, K.M., Zhou, Z.H. "Isolation Forest." *ICDM 2008*; extended version in *ACM TIST*, 2012. `[CONFIRMED]`

**Local Outlier Factor (LOF)**
- Breunig, M.M., Kriegel, H.P., Ng, R.T., Sander, J. "LOF: Identifying Density-Based Local Outliers." *SIGMOD 2000*. `[CONFIRMED]`

**One-Class SVM**
- Schölkopf, B., Platt, J.C., Shawe-Taylor, J., Smola, A.J., Williamson, R.C. "Estimating the Support of a High-Dimensional Distribution." *Neural Computation*, 13(7), 2001. `[CONFIRMED]`

---

## Part B: Prior-Art Threat Assessment Table (Revised)

| Source | Covers AD Identity State | Covers Endpoint Patch | Covers Vulnerability Data | Models Freshness/Missingness | Public/Reproducible | Formal Academic Publication | Threat to Novelty | Required Differentiation |
|---|---|---|---|---|---|---|---|---|
| LANL Unified Host/Net (2017) | Partial (auth only) | No | No | No | Yes | Yes (arXiv) | Low | Auth events ≠ identity hygiene state |
| CERT Insider Threat | Partial (logon only) | No | No | No | Yes | Yes (SPW 2013) | Low | Insider behavior ≠ hygiene posture |
| CIC-IDS2018 | No | No | No | No | Yes | Yes (ICISSP 2018) | Low | Network IDS; different domain |
| DARPA TC | No | No | No | No | Partial | No (VERIFY) | Low | APT provenance; different domain |
| Mordor / Security Datasets | No (attack events only) | No | No | No | Yes | No (tool/project) | Medium | Attack emulation ≠ hygiene state; no patch/vuln/freshness |
| BOTSv3 | No | No | No | No | Yes (CC0) | No | Low | CTF training; no formal benchmark |
| Defender for Identity | No (attack detection) | No | No (within scope) | No | No (closed) | No | High (framing) | Open benchmark ≠ closed product; hygiene state ≠ attack detection |
| Entra ID Protection | Cloud only | No | No | No | No (closed) | No | Medium | On-prem + endpoint + vuln scope not covered |
| Splunk UBA / Exabeam | Partial (closed) | Partial (closed) | Partial (closed) | No | No (closed) | No | Medium | No reproducible artifact; no controlled evaluation |
| Microsoft Sentinel | Partial (via connectors) | Partial (via connectors) | Partial | No | No (closed) | No | Medium | SIEM ≠ research benchmark |
| BloodHound | Yes (attack paths) | No | No | No | Yes (OSS) | No (tool) | Medium | Attack path enumeration ≠ hygiene anomaly scoring |
| DOMINANT / AnomalyDAE | No (generic method) | No | No | No | Yes | Yes (SDM 2019 / ICASSP 2020) | Low | Method only; no cyber-hygiene benchmark application |
| MITRE ATT&CK | Framework | — | — | — | Yes | Yes (MITRE 2018) | None | Framework, not a dataset |
| CISA BOD 22-01 / 23-01 | Guidance | Guidance | Guidance | No | Yes | Guidance doc | None | Normative context |
| NIST SP 800-40 / 800-53 / 800-207 | Guidance | Guidance | Guidance | No | Yes | Guidance doc | None | Normative context |
| Verizon DBIR 2026 | No | Yes (aggregate) | Yes (aggregate) | No | Yes | Industry report | Low | Provides aggregate priors; not a benchmark |
| NVD | No | No | Yes (raw) | No | Yes | Gov database | None | Data source for CVE priors |
| No joint cyber-hygiene benchmark found | — | — | — | — | — | — | **Gap confirmed** | — |

---

## Part C: Gap Survival Analysis (Step 1 §7 Contributions)

### C1 — Synthetic identity–endpoint–patch–vulnerability cyber-hygiene telemetry generator

**Verdict: SURVIVES.**

No existing public dataset or tool jointly generates identity state (AD), endpoint patch posture, vulnerability records, telemetry freshness, and missingness in a single seeded, reproducible pipeline. Mordor provides attack-emulation telemetry; CERT provides behavioral insider-threat logs; neither provides hygiene-state telemetry. The gap is unambiguous.

**Remaining risk:** Reviewers may question synthetic realism. Mitigation: document all structural assumptions, cite published aggregate statistics (DBIR 2026 patch lag, NVD CVE age distributions), and conduct sensitivity sweeps over generative parameters.

---

### C2 — Cyber-hygiene anomaly taxonomy

**Verdict: SURVIVES.**

No published paper formally taxonomizes cyber-hygiene anomaly classes across AD identity state + endpoint patch posture + vulnerability exposure + telemetry freshness as a joint ML-task definition. MITRE ATT&CK covers adversary technique taxonomy. CIS Benchmarks cover prescriptive hygiene controls. Neither defines a joint anomaly taxonomy suitable for benchmark task construction.

**ATT&CK mapping caveat:** Map hygiene classes to ATT&CK *enabling conditions* only, not to technique detection claims (e.g., "stale privileged account → condition enabling T1078.002" is defensible; "detects T1078.002" is not).

---

### C3 — Benchmark tasks under stale/missing telemetry

**Verdict: SURVIVES STRONGLY.**

No existing benchmark systematically varies telemetry freshness, source missingness, and inventory mismatch as first-class controlled evaluation conditions for any ML anomaly-detection task, let alone for a joint identity/endpoint/patch/vulnerability hygiene problem. This is the strongest and most distinctive contribution.

---

### C4 — Comparative evaluation of unsupervised anomaly detectors under class imbalance

**Verdict: PARTIALLY SURVIVES.**

The *methods* (Isolation Forest, LOF, OCSVM, autoencoders) are well-established. Comparative evaluations of these methods on generic anomaly detection are common. The *application domain* — cyber-hygiene signals under class imbalance, stale/missing telemetry, and the joint identity/endpoint/patch/vulnerability schema — is novel. The contribution is in the *benchmark application and evaluation conditions*, not in the detection methods themselves.

**Paper framing note:** Do not claim novelty on the methods; claim novelty on the evaluation protocol and findings within this domain.

---

### C5 — Joint identity–endpoint–vulnerability hybrid risk score

**Verdict: PARTIALLY SURVIVES.**

Microsoft Secure Score, Qualys TruRisk, and similar vendor products compute hybrid risk scores, but all are closed and none is a reproducible research artifact. An open, reproducible hybrid scorer — exposed as a baseline, not as a product claim — survives as a contribution. However, this is the *weakest* of the five candidates and adds implementation complexity. Recommended for Step 3: include as a baseline within C4 rather than a standalone contribution.

---

### C6 — Reproducibility and audit pipeline

**Verdict: SURVIVES** but is better positioned as an *enabler* of C1–C4 than a standalone contribution. Consistent with Paper 1's reproducibility ethos; do not overclaim as a novel methodology.

---

### C7 — Failure-aware / negative-result reporting

**Verdict: SURVIVES.**

Failure-aware reporting (explicit documentation of conditions where ML does not outperform simple rule baselines) is structurally underrepresented in cybersecurity ML literature, where papers disproportionately report positive results. This contribution has methodological and practical value for public-sector SOC teams making tool-investment decisions.

---

## Part D: Locked Contribution Menu

After falsification, the following **5 contributions** are locked for Paper 3:

| # | Contribution | Gap survival |
|---|---|---|
| **C1** | Synthetic identity–endpoint–patch–vulnerability cyber-hygiene telemetry generator (seeded, reproducible, schema-documented) | SURVIVES |
| **C2** | Cyber-hygiene anomaly taxonomy (formal definitions, ATT&CK enabling-condition mapping, benchmark-task linkage) | SURVIVES |
| **C3** | Benchmark task suite under stale/missing telemetry (tasks T1–T7 parameterized over freshness, missingness, imbalance, label sparsity) | SURVIVES STRONGLY |
| **C4** | Comparative evaluation of unsupervised anomaly detectors under class imbalance (rule baseline, Isolation Forest, LOF, OCSVM, autoencoder, temporal z-score, graph baseline; failure-aware reporting) | PARTIALLY SURVIVES — novelty in evaluation protocol and domain, not methods |
| **C7** | Failure-aware (negative-result) evaluation protocol | SURVIVES |

**Dropped from standalone status:**
- C5 (hybrid risk score): Folded into C4 as a baseline scorer, not a standalone contribution.
- C6 (reproducibility pipeline): Treated as an enabler of C1–C4; mentioned in paper but not foregrounded as a contribution.

---

## Part E: Residual [VERIFY] Items Requiring Manual Resolution Before Submission

The following items could not be fully confirmed without library access and must be resolved before submitting or circulating a draft:

1. DARPA TC dataset — confirm current public access point and cite the most authoritative associated publication.
2. AnomalyDAE (Fan, Zhang, Li — ICASSP 2020) — confirm full proceedings citation.
3. PyGOD library — confirm arXiv or JMLR publication and cite if used as an implementation tool.
4. CIS Benchmarks for Active Directory — confirm current version number and citation format.
5. Vulnerability life-cycle / patch deployment academic papers — search specifically for peer-reviewed papers on enterprise patch lag distributions (not DBIR aggregate).

---

*End of Step 2 Prior-Art Falsification Report.*
