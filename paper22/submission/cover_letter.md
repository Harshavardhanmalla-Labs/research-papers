# Cover letter — Expert Systems with Applications

**Manuscript:** An Explainable Neuro-Symbolic Expert System for Autonomous
Cyber-Risk Prioritization in Smart-City and Industrial-IoT Infrastructure

**Author:** Harshavardhan Malla (Independent Researcher) — harshavardhanmalla75@gmail.com

---

Dear Editor-in-Chief,

I am pleased to submit the enclosed manuscript for consideration as an original
research article in *Expert Systems with Applications*.

**The problem.** Operators of smart-city and industrial-IoT estates must decide,
every maintenance window, which of tens of thousands of (asset, vulnerability)
pairs to remediate under a fixed capacity budget. The dominant public signal, the
Exploit Prediction Scoring System (EPSS), is asset-agnostic by design, and the
machine-learning ensembles that augment it are accurate but opaque — an operator
cannot see *why* a given item was ranked, which is untenable for safety-critical
infrastructure subject to audit.

**The contribution.** We present ENSES, a neuro-symbolic expert system that couples
(i) a symbolic knowledge graph linking CVEs to weakness classes, attacker tactics,
and asset classes, (ii) a neural retrieval tier over real exploited-vulnerability
descriptions, and (iii) a glass-box additive inference engine whose every decision
decomposes into human-readable contributions. On a real public corpus of 203,174
CVEs with FIRST.org EPSS and CISA Known-Exploited-Vulnerability metadata, ENSES
attains a harm-weighted Precision@100 of 0.871, exceeding a strong gradient-boosted
ensemble (0.857; the improvement's BCa 95% confidence interval excludes zero) and
EPSS-only ranking (0.208), while running roughly five times faster (4.5 µs/decision)
and explaining each ranking. An ablation isolates the contribution of each tier.

**Fit to ESWA.** The work is an applied expert system in the journal's core sense:
a knowledge-based, explainable decision-support system validated on real-world data
for a high-consequence application. It directly addresses the journal's interest in
intelligent, transparent systems that practitioners can deploy and trust.

**Assurances.** This manuscript is original, is not under consideration elsewhere,
and has not been published before. The evaluation combines a real public
vulnerability corpus with a transparently generated, differentially-private estate
model (no proprietary or personal data); all code, data pointers, and frozen
results are released so every reported number reproduces deterministically from
fixed seeds. The author declares no conflict of interest and received no funding.

Thank you for considering this submission.

Sincerely,
Harshavardhan Malla

---

## Suggested reviewers
Researchers with directly relevant expertise in vulnerability prioritization,
exploit prediction, and explainable security ML. None are recent collaborators.
*(Please verify current affiliations and obtain contact emails before submission —
the names and institutions below are public, but emails should not be guessed.)*

- **Jay Jacobs**, Cyentia Institute — co-creator of EPSS; exploit-likelihood modeling.
- **Sasha Romanosky**, RAND Corporation — security economics, vulnerability scoring.
- **Jonathan M. Spring** — stakeholder-specific vulnerability categorization (SSVC).
- **Luca Allodi**, Eindhoven University of Technology — empirical vulnerability exploitation.
- **Tudor Dumitraș**, University of Maryland — data-driven exploit prediction.
- **Fabio Massacci**, University of Trento / Vrije Universiteit Amsterdam — vulnerability risk and economics.

## Opposed reviewers
None.
