# Cover letter — Computers & Security

**Manuscript:** HygienePrio: Integrating Host-Level Hygiene Posture into
EPSS-Weighted (Host, CVE) Vulnerability Prioritization

**Author:** Harshavardhan Malla (Independent Researcher) — harshavardhanmalla75@gmail.com

---

Dear Editor-in-Chief,

I am pleased to submit the enclosed manuscript for consideration as an original
research article in *Computers & Security*.

**The problem.** Capacity-constrained remediation teams must decide which
(host, CVE) pairs to patch within each maintenance window, yet the dominant
public triage signal — the Exploit Prediction Scoring System (EPSS) — is
asset-agnostic by design: it estimates per-CVE exploit likelihood without regard
to whether the affected host is actively managed, carries high patch debt, or is
exposed through privileged Active Directory relationships. The same CVE on a
freshly-telemetered, heavily-patched workstation and on an unmanaged endpoint
with stale data and over-privileged group memberships receives an identical
ranking. The signal missing from CVE-level triage is therefore dynamic,
host-level hygiene posture rather than additional CVE-level features.

**The contribution.** We present HygienePrio, a scoring framework that integrates
a three-dimensional Hygiene Risk Score (HRS) — patch posture, AD exposure state,
and telemetry freshness — into an EPSS-weighted (host, CVE) scorer with an
explicit interaction term, calibrated by pre-registered grid search on held-out
fleet seeds. On a pre-registered, fully reproducible benchmark across 25
independent fleet seeds, HygienePrio raises mean Precision@50 from EPSS-only's
0.202 to 0.509 — an approximately 31-percentage-point gain under
capacity-constrained schedules — with non-overlapping BCa 95% confidence
intervals and an improvement on every one of the 25 seeds (mean per-seed gain
30.7 pp). The advantage is largest at the tightest capacity (P@50) and remains
substantial at P@100 (0.458 vs. 0.199) and P@250 (0.420 vs. 0.215). An ablation
isolates patch posture as the load-bearing hygiene dimension (≈20 pp drop at
P@50), well above AD exposure (≈9 pp) and telemetry freshness (≈2 pp, CIs
overlapping). We further validate the scorer against real public EPSS and
Known-Exploited-Vulnerability (KEV) attribute distributions drawn from a
203,174-CVE snapshot: there the aggregate margin shrinks to +2.4 pp, but
host-level discrimination at major-CVE disclosure moments — exactly when
remediation capacity is scarcest — persists, and we characterize the regimes in
which hygiene augmentation helps and those in which it is dominated by capacity.

**Fit to Computers & Security.** The work sits squarely in the journal's core
scope: EPSS-weighted vulnerability prioritization, host-level cyber-hygiene
posture, and capacity-constrained remediation for security operations. It speaks
directly to risk-based vulnerability management and CISA prioritization guidance,
and offers operations teams an interpretable, deployable ordering signal together
with a falsifiable benchmark on which calibrated studies can build.

**Assurances.** This manuscript is original, is not under consideration elsewhere,
and has not been published before. The evaluation combines a real public EPSS/KEV
corpus (a frozen 203,174-CVE snapshot) with a transparently generated, synthetic
government-shaped fleet benchmark (no proprietary or personal data); the scorer,
the benchmark generator, and the frozen results are released so that every
reported number reproduces deterministically from fixed seeds. The author
declares no conflict of interest and received no funding.

Thank you for considering this submission.

Sincerely,
Harshavardhan Malla

---

## Suggested reviewers
Researchers with directly relevant expertise in exploit prediction, EPSS,
vulnerability prioritization, and security operations. None are collaborators.
*(Please verify current affiliations and obtain contact emails before submission —
the names and institutions below are public, but emails should not be guessed.)*

- **Jay Jacobs**, Cyentia Institute — co-creator of EPSS; data-driven exploit-likelihood modeling.
- **Sasha Romanosky**, RAND Corporation — security economics; vulnerability scoring and remediation policy.
- **Jonathan M. Spring**, CISA / CERT — Stakeholder-Specific Vulnerability Categorization (SSVC) and decision-tree prioritization.
- **Luca Allodi**, Eindhoven University of Technology — empirical measurement of vulnerability exploitation in the wild.
- **Tudor Dumitraș**, University of Maryland — data-driven exploit prediction and vulnerability lifecycle analysis.
- **Fabio Massacci**, University of Trento / Vrije Universiteit Amsterdam — vulnerability risk economics and exploitation prediction.

## Opposed reviewers
None.
