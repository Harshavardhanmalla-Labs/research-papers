# A Context-Aware Ensemble Learning Framework for Vulnerability Prioritization in Critical Infrastructure

**Harshavardhan Malla** — Independent Researcher

> **Status: Ready for publication.** The full manuscript is in the **Submission** tab (PDF); the reproducible evaluation code is in **src/** and the frozen per-seed results in **results/primary_v1/**.

## Abstract

This study introduces a context-aware machine learning framework for vulnerability prioritization in critical infrastructure. While current practices rely on static metrics such as CVSS, they lack environmental context and exploitability signal. We propose an ensemble of Random Forest and XGBoost that fuses vulnerability metadata, threat-intelligence indicators (KEV membership, public proof-of-concept, ATT&CK mapping), and environmental context (asset criticality, exposure, patch age, vulnerability density). To support reproducibility we evaluate on a pre-registered synthetic benchmark that models 18 monthly Patch Tuesday cycles across a 50,000-endpoint government fleet, with all code and frozen results released. Across 25 seeds the ensemble attains a Precision@50 of 0.74 against 0.22 for CVSS-only ranking, lowers the high-risk miss rate from 0.67 to 0.18, and raises within-window SLA compliance from 0.64 to 0.98; under a capacity-constrained remediation scheduler it cuts mean time to remediate by 62% (6.2 to 2.3 days). Every gain is supported by a pre-registered hypothesis whose bias-corrected and accelerated bootstrap interval excludes zero.

**Index Terms:** Patch Tuesday, machine learning-based prioritization, CVE, critical infrastructure, threat intelligence integration, Random Forest, XGBoost, vulnerability management automation.

## Key results (reproducible synthetic benchmark, 25 seeds)

- **Precision@50 of 0.74** for the proposed ensemble versus **0.22** for CVSS-only ranking.
- **High-risk miss rate 0.18** (vs 0.67) and **false-positive rate 0.12** (vs 0.18).
- **MTTR cut 62%** (6.2 to 2.3 days) and **SLA compliance lifted 0.64 to 0.98** under a capacity-constrained scheduler.
- **All 5 pre-registered hypotheses supported** — every BCa 95% confidence interval excludes zero.
- **Random Forest + XGBoost ensemble** fusing CVE metadata, threat-intelligence indicators, and environmental context.
- End-to-end automation: risk-scoring wired into **SCCM and Intune** remediation workflows.

## Contribution

The framework moves vulnerability prioritization from static, severity-only scoring (CVSS) to a context-aware ensemble that incorporates exploitability and asset context, then closes the loop with automated, audit-ready remediation. The evaluation is fully reproducible: a seeded synthetic fleet, a real RF+XGBoost ensemble against CVSS/EPSS/random baselines, a capacity-constrained remediation scheduler, and pre-registered hypotheses with BCa intervals — the same integrity bar as the rest of this research program.

*Read the full manuscript in the Submission tab; reproduce from `src/run_evaluation.py`.*
