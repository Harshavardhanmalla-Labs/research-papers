# Cover letter — Computers & Security

**Manuscript:** Patch Tuesday Triage: Asset Criticality, Not Early Exploit
Signal, Drives Emergent-Risk Vulnerability Prioritization on Government Fleets

**Author:** Harshavardhan Malla (Independent Researcher) — harshavardhanmalla75@gmail.com

---

Dear Editor-in-Chief,

I am pleased to submit the enclosed manuscript for consideration as an original
research article in *Computers & Security*.

**The problem.** On the second Tuesday of each month, a government patch team
must decide, at disclosure time, which of a batch of newly disclosed CVEs to
deploy first under a fixed remediation capacity. The natural assumption is that
the exploit-likelihood signal should govern that decision. But at disclosure the
Exploit Prediction Scoring System (EPSS) score is immature — it is revised upward
as evidence accrues over the days after disclosure, and entry into the CISA Known
Exploited Vulnerabilities (KEV) catalog lags the disclosure event. A team that
ranks its Patch Tuesday queue by the day-0 EPSS observation is therefore acting on
a noisy, biased-low estimate of the risk that will materialize over the very window
it is trying to protect. The signal the intuition most wants to trust is the one
least trustworthy at the moment the decision must be made.

**The contribution.** This paper presents the first pre-registered, reproducible
demonstration that, in the scarce-capacity disclosure-time regime, *asset
criticality dominates exploit-likelihood* for patch-window triage, together with
the operational decision rule that follows. Using a pre-registered simulation on a
synthetic 830-host government fleet whose EPSS and KEV signal is resampled from a
frozen real corpus of 203,174 CVEs — with the immature day-0 observation produced
by a pre-registered maturation model — context-weighted triage raises
mission-weighted precision at the top 50 from 0.234 (a context-blind day-0 EPSS
baseline) to 0.298, a gain of 6.48 points with a 95% BCa interval of [4.9, 7.8]
that clears the pre-registered five-point bar. The Asset Context Score places its
dominant weight (0.5 of three terms) on criticality. Three ablations isolate the
mechanism: dropping the day-0 EPSS observation changes precision by only 1.52
points, so the immature exploit signal is nearly redundant; removing the
asset-context factor erases the entire gain, confirming the advantage is asset
weighting rather than a better treatment of the exploit signal; and the advantage
is a scarce-capacity effect, decaying from 6.48 points at the top 50 to 0.1 point
at the top 250. Context-weighted triage with stable signals (0.298) nearly matches
a matured-EPSS oracle (0.302) that no day-0 method can see. A closed-form analysis
of the inverse-variance fusion and the context multiplier explains why. The
resulting recommendation is direct: at disclosure time, weight the patch queue by
asset criticality immediately rather than waiting for the exploit signal to mature.

**Fit to *Computers & Security*.** The work is squarely within the journal's scope:
it addresses enterprise patch management and the day-0 triage decision faced in
real security operations, grounds the asset signal in categorization data agencies
already hold under FIPS 199, SP 800-60, and the CISA Binding Operational Directives,
and yields an immediately deployable, asset-criticality-driven prioritization rule.
It contributes both a measured result and an adversarial-robustness argument
relevant to practitioners ordering scarce remediation capacity.

**Assurances.** This manuscript is original, is not under consideration elsewhere,
and has not been published before. The study is pre-registered: the hypotheses,
thresholds, model constants, maturation model, and evaluation seed range were fixed
in a dated protocol before any result on the evaluation seeds (500–524) was
inspected. Every interval is a bias-corrected and accelerated (BCa) bootstrap
interval, and all code, data pointers, and frozen result tables are released so that
every reported number reproduces deterministically from the fixed seeds. No
operational, employer, or audit data is used. The author declares no conflict of
interest and received no funding.

Thank you for considering this submission.

Sincerely,
Harshavardhan Malla
Independent Researcher
harshavardhanmalla75@gmail.com

---

## Suggested reviewers
Researchers with directly relevant expertise in vulnerability and patch
prioritization, exploit prediction, security operations, and asset/risk
management. None are collaborators.
*(Please verify current affiliations and obtain contact emails before submission —
the names and institutions below are public, but emails should not be guessed.)*

- **Jay Jacobs**, Cyentia Institute — co-creator of EPSS; exploit-likelihood modeling and vulnerability prioritization.
- **Sasha Romanosky**, RAND Corporation — security economics and vulnerability scoring; co-author of EPSS.
- **Jonathan M. Spring**, CISA — stakeholder-specific vulnerability categorization (SSVC) and decision-driven remediation.
- **Luca Allodi**, Eindhoven University of Technology — empirical measurement of vulnerability exploitation and risk-based prioritization.
- **Tudor Dumitraș**, University of Maryland — data-driven exploit prediction and large-scale vulnerability analysis.
- **Fabio Massacci**, University of Trento / Vrije Universiteit Amsterdam — vulnerability risk, exploitation economics, and patch management.

## Opposed reviewers
None.
