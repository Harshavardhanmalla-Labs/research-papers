# Cover letter — ACM Digital Threats: Research and Practice (DTRAP)

**Manuscript:** HygieneBench: A Reproducible Synthetic Benchmark for Cyber-Hygiene
Anomaly Detection Across Identity, Endpoint, and Patch Telemetry

**Author:** Harshavardhan Malla (Independent Researcher) — harshavardhanmalla75@gmail.com

---

Dear Editors-in-Chief,

I am pleased to submit the enclosed manuscript for consideration in *ACM Digital
Threats: Research and Practice*. The work is a reproducible benchmark contribution
— a dataset, generator, and evaluation methodology — aimed squarely at practical,
reproducible threat research.

**The problem.** Security operations centers must continuously monitor cyber-hygiene
posture — stale privileged accounts, dormant-account reactivations, endpoint
coverage gaps, patch-noncompliance clusters, and telemetry missingness — yet the
anomaly-detection research community has no dedicated public benchmark for this
problem. Existing security datasets (LANL Unified Host and Network, CERT Insider
Threat, CICIDS, attack-emulation repositories) model network intrusion or
insider-threat telemetry but do not treat identity hygiene state, patch posture,
vulnerability exposure, or telemetry freshness as first-class evaluation axes.
Commercial platforms address related detection but release no benchmark data.
Consequently, researchers cannot compare hygiene-detection methods under controlled
conditions, and there is no principled accounting of when unsupervised ML actually
adds value over simpler rules — a question with direct operational cost
implications.

**The contribution.** We present HygieneBench, an open, reproducible benchmark that
jointly covers Active Directory identity state, endpoint patch posture,
vulnerability exposure, and telemetry freshness. It comprises (i) a fully open,
seeded synthetic telemetry generator spanning eleven entity/event tables;
(ii) a taxonomy of twelve cyber-hygiene anomaly classes (AH-01 through AH-12) with
ATT&CK enabling-condition mappings; (iii) a suite of seven evaluation tasks (T1–T7)
under five telemetry conditions (baseline, fresh, stale, missing, unsupervised);
and (iv) an 810-run comparative evaluation of eight methods — a rule baseline,
hybrid risk scorer, Isolation Forest, Local Outlier Factor, One-Class SVM, a linear
autoencoder, population-level temporal z-score, and a graph-augmented Isolation
Forest. Applying a pre-registered failure protocol (Δ < 0.05 AP and Δ < 0.05 P@k in
≥ 2/3 seeds), we report that **83.8% of (condition, task, method) configurations
fail to improve on the rule baseline**, with ML adding meaningful signal only on
T2 (group-membership-drift detection; best ML +0.185 AP over rule) and T5
(patch-vulnerability hygiene; best ML +0.210 AP over rule). Telemetry staleness
consistently degrades detection relative to baseline. We deliberately report these
negative results in full rather than filtering them.

**Fit to DTRAP.** DTRAP values practical, reproducible threat research that
practitioners can act on. HygieneBench is exactly that: an artifact — generator,
datasets, and evaluation harness — that lets the community reproduce, compare, and
extend hygiene-detection methods, plus an honest, failure-aware accounting of when
ML deployment is and is not justified for SOC hygiene monitoring. The negative-result
reporting directly serves operators deciding whether to invest in ML over
rule maintenance.

**Assurances.** This manuscript is original, is not under consideration elsewhere,
and has not been published before. The benchmark uses **no employer, production, or
personal data at any stage**: all telemetry is synthetic, generated from publicly
citable structural priors (NIST NVD severity distributions, Verizon DBIR 2026
patch-lag aggregates, CISA BOD 23-01 telemetry-cadence requirements), with the full
generation distributions documented in the paper. The generator, datasets, analysis
code, and frozen result tables are openly released, and every reported number
regenerates deterministically from fixed seeds. The author declares no conflict of
interest and received no funding.

Thank you for considering this submission.

Sincerely,
Harshavardhan Malla
Independent Researcher

---

## Suggested reviewers
Researchers with directly relevant expertise in security dataset construction,
reproducible security evaluation, and anomaly detection for security operations.
None are collaborators of the author.
*(Please verify current affiliations and obtain contact emails before submission —
the names and institutions below are public, but emails should not be guessed.)*

- **Arash Habibi Lashkari**, York University — co-author of the CICIDS intrusion
  datasets; security dataset generation and benchmarking methodology.
- **Brian Lindauer**, Carnegie Mellon SEI/CERT — co-author of the CERT Insider
  Threat synthetic datasets; principled generation of labeled security data.
- **Roberto Rodriguez** — creator of Mordor / Security-Datasets and OSSEM; security
  telemetry datasets and detection evaluation.
- **Leman Akoglu**, Carnegie Mellon University — anomaly and outlier detection
  research and benchmarking, including graph outlier detection.
- **Sasha Romanosky**, RAND Corporation — security economics and the operational
  cost/value tradeoffs of vulnerability and hygiene remediation.
- **Tudor Dumitraș**, University of Maryland — data-driven, empirical security
  measurement and reproducible evaluation.

## Opposed reviewers
None.
