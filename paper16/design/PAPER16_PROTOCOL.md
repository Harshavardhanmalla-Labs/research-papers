# Paper 16: Pre-Registration and Research Protocol

**Title:** Multivariate Machine Learning for Cyber-Hygiene Anomaly Detection Across Active
Directory, Endpoint, and Patch Telemetry
**Short title:** Hygiene Anomaly Detection
**Author:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management / ACM Digital Threats
**Pre-registration date:** 2026-06-20
**Date locked:** 2026-06-20, before any result on the evaluation seeds (700 to 724) was inspected.

---

## 1. Motivation

Government security operations teams watch large endpoint fleets through three telemetry
channels: Active Directory (privileged logons, group churn, stale admin accounts), endpoint
posture (process anomalies, unsigned binaries, configuration drift), and patch state (patch
debt, days since patch, telemetry staleness). A host that is compromised or badly misconfigured
shows up as an anomaly in this telemetry. The operational question is whether multivariate
machine-learning anomaly detection earns its added complexity over the per-signal threshold
rules that operations teams already run, and if so, when.

The hypothesis we set out to test is that the answer depends on the structure of the anomaly. A
blatant single-channel anomaly, such as a sudden spike in patch debt, is caught by a simple
per-feature rule. A subtle cross-channel anomaly, where every channel shifts slightly but no
single channel crosses a threshold, is exactly the case a joint multivariate detector should
catch and a per-feature rule should miss. If true, the practical guidance is specific: deploy
multivariate detection for the subtle, compromise-like cases and keep cheap rules for the
obvious ones.

---

## 2. Hypotheses

**H1 (Primary).** On cross-dimensional anomalies, the best multivariate detector exceeds the best
per-feature rule baseline on average precision by at least 0.10, across 25 evaluation seeds, with
a BCa interval excluding zero.

**H2 (Specificity).** On single-dimension anomalies, the per-feature rule baseline is not beaten
by the multivariate detectors by more than 0.05 average precision. The multivariate advantage is
specific to cross-dimensional structure, not a general superiority.

**H3 (Mechanism).** On cross-dimensional anomalies, joint detectors that model the feature
covariance (Mahalanobis, Isolation Forest, One-Class SVM, Local Outlier Factor) beat a
structure-blind detector that only counts per-feature exceedances, by a BCa-separated margin.
The cross-dimensional gain requires joint modeling, not just aggregation of per-feature signals.

**H4 (Mixed realism).** On a realistic mixture of both anomaly types, the best multivariate
detector beats the best rule baseline on average precision, but by less than the
cross-dimensional-only margin, because the single-dimension cases are caught equally well by
both. Reported honestly whatever the sign.

---

## 3. Data

A synthetic fleet of 1{,}500 hosts per seed. Each host has a 12-dimensional standardized
cyber-hygiene telemetry vector, four features in each of three channels: Active Directory,
endpoint, and patch. Normal hosts draw from a multivariate baseline with a within-channel
correlation of 0.70. Anomalous hosts (8 percent prevalence) are of two pre-registered types:

- **Single-dimension anomaly (SDA):** a strong shift (mean 3.0 standard deviations) applied to
  the features of one randomly chosen channel only. Individually threshold-crossing.
- **Cross-dimensional anomaly (CDA):** a correlation-structure violation. The host's twelve
  features are drawn independently from the same standard-normal marginal as normal hosts, so
  each feature is individually unremarkable, but the joint pattern breaks the within-channel
  correlation that normal hosts exhibit. This is the canonical case of an anomaly that is
  invisible to per-feature inspection but visible to a joint detector.

Three evaluation conditions are run on the same seeds: SDA-only, CDA-only, and a 50/50 mixture.
No employer, operational, or real telemetry data is used; all features are synthetic with
documented distributions.

---

## 4. Detectors

All detectors output a continuous per-host anomaly score; evaluation is threshold-free
(average precision over the ranking), so no detector gains from threshold tuning.

| Detector | Type |
|---|---|
| Rule-Max | per-feature: maximum robust z-score across features |
| Rule-Count | structure-blind aggregate: count of features with robust z above 2.5 |
| Mahalanobis | joint parametric: Mahalanobis distance under a fitted covariance |
| Isolation Forest | joint, tree-based [Liu et al. 2008] |
| One-Class SVM | joint, kernel-based [Scholkopf et al. 2001] |
| Local Outlier Factor | joint, density-based [Breunig et al. 2000] |

Detector hyperparameters are fixed at library defaults (Isolation Forest 200 trees; One-Class
SVM RBF kernel, nu 0.1; Local Outlier Factor 20 neighbors) and are not tuned on any seed.
"Multivariate" refers to the four joint detectors; "rule baseline" to Rule-Max and Rule-Count.

---

## 5. Metrics

Primary: average precision (area under the precision-recall curve), appropriate for rare-anomaly
ranking [Davis and Goadrich 2006]. Secondary: precision at the true anomaly count. Mean with 95
percent BCa bootstrap interval (10{,}000 resamples) over 25 seeds; interval non-overlap is the
evidentiary standard; no significance testing.

---

## 6. Failure Criteria

If the best multivariate detector does not exceed the best rule baseline by at least 0.05 average
precision on cross-dimensional anomalies, declare H1 null and report the characterization. If a
rule baseline beats the multivariate detectors on cross-dimensional anomalies, report that
counter-result directly. Do not tune detector hyperparameters or re-draw the anomaly model to
reach a threshold.

---

## 7. Reproducibility

A self-contained code and frozen-result artifact accompanies this paper in its own public
repository. All randomness is seeded; the run manifest records seeds, the anomaly model
constants, and detector settings.

---

## 8. Threats and Limitations

The fleet and its telemetry are synthetic with documented distributions, so absolute average
precision values are not field measurements; the comparative results across detectors and
anomaly types are the contribution. The anomaly model defines what cross-dimensional means, and
real compromise telemetry may differ; the structural finding (joint modeling helps on joint
anomalies) is more robust than the magnitudes. Detector defaults are fixed rather than tuned,
which is conservative for the multivariate detectors.

---

## 9. Pre-Registration Attestation

Locked 2026-06-20 before any result on the evaluation seeds 700 to 724 was inspected. Detector
settings and anomaly-model constants are fixed; no hyperparameter is tuned on any seed. No real
telemetry data is used.
