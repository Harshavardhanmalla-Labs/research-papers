# A Context-Aware Ensemble Learning Framework for Vulnerability Prioritization in Smart-City and Industrial Cyber-Physical Infrastructures

**Harshavardhan Malla** — Independent Researcher, Phoenix, AZ 85001, USA

> **Status: Ready for submission.** Target journal: **Expert Systems with Applications (ESWA)**, Elsevier Q1. The full manuscript is in the **Submission** tab (PDF); figures in `submission/figures_p20/`.

## Abstract

The exponential growth in disclosed Common Vulnerabilities and Exposures (CVEs) has made static, severity-only prioritization insufficient for operators of smart-city and industrial cyber-physical systems (CPS). Traditional reliance on the Common Vulnerability Scoring System (CVSS) ignores real-time exploitability, asset exposure, and operational context, leaving critical infrastructure endpoints exposed during the interval between disclosure and remediation. This paper presents a context-aware ensemble machine learning framework that combines Random Forest (RF) and XGBoost classifiers under a stacked fusion scheme to produce fine-grained, actionable vulnerability priority scores. The framework ingests four complementary feature streams: static CVE metadata from the National Vulnerability Database (NVD), dynamic threat intelligence from the CISA Known Exploited Vulnerabilities (KEV) catalog, public proof-of-concept exploit repositories and MITRE ATT&CK technique mappings, and environmental telemetry reflecting asset criticality, network exposure, patch age, and historical vulnerability density. These signals are unified through an empirically calibrated risk score formula — RiskScore = 0.3M + 0.3A + 0.2E + 0.2B — whose weights were tuned via grid search and validated through SHAP analysis. The model is trained and evaluated on an 18-month operational dataset spanning approximately 50,000 mixed IT/OT endpoints across three remediation cycles. The proposed system achieves Precision@50 = 0.94, reduces Mean Time to Remediate (MTTR) by 70%, and raises SLA compliance from 68% to 93%, outperforming CVSS-only baselines, Logistic Regression, VulnPredict, and CVE-BERT on all primary metrics. A second evaluation against publicly available EPSS data yields AUC-ROC = 0.91, confirming cross-dataset generalizability.

**Keywords:** Vulnerability prioritization, ensemble learning, Random Forest, XGBoost, SHAP explainability, cyber-physical systems, smart city security, industrial control systems, EPSS, CVE triage, threat intelligence

## Key Results

- **Precision@50 = 0.94** vs 0.85 for nearest baseline (CVE-BERT)
- **MTTR reduced 70%** across three operational remediation cycles
- **SLA compliance lifted from 68% to 93%**
- **AUC-ROC = 0.91** on independent EPSS v3 validation dataset (cross-dataset generalizability)
- **SHAP analysis** confirms exploit availability and asset criticality dominate prioritization decisions
- RiskScore weights (0.3, 0.3, 0.2, 0.2) confirmed optimal via 22-combination grid search
- Outperforms CVSS-only, Logistic Regression, VulnPredict, and CVE-BERT on all metrics

## Contributions

- **C1. Formal prioritization framework** — vulnerability prioritization defined as ranking function f: V → ℝ with ensemble fusion objective derived from first principles
- **C2. Four-stream feature architecture** — 28 features spanning static CVE metadata, live threat intelligence, OT/ICS environmental telemetry, and compliance urgency signals
- **C3. Empirically calibrated risk score** — RiskScore = 0.3M + 0.3A + 0.2E + 0.2B derived via grid search and confirmed by SHAP
- **C4. Cross-dataset EPSS validation** — AUC-ROC = 0.91 on public FIRST.org EPSS v3 data without retraining
- **C5. Operational deployment integration** — direct connection to industrial patch orchestration workflows, eliminating the manual export gap

*Read the full manuscript in the Submission tab.*
