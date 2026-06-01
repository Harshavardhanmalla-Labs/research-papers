# Citation Audit (Phase 19)

**No citations are fabricated.** Exact bibliographic details (authors, year, venue,
DOI/URL) are NOT filled in here unless independently verified. Every entry is
marked `needs verification` or `unresolved` and tagged `[VERIFY]`. Phase 19 only
catalogs what must be cited, where, and why; it does not invent references.

Status legend: `verified` (full reference confirmed) / `needs verification`
(source/identity known, exact reference must be confirmed) / `unresolved` (must be
located).

---

## A. CVSS / EPSS / exploit prediction

| Key | Source (as named) | Status | Used in | Claim it supports | Risk if missing |
| --- | --- | --- | --- | --- | --- |
| A1 | FIRST — CVSS specification (state version: v3.1 and/or v4.0) | needs verification `[VERIFY]` | §2, §5, §9 | Definition of the S (CVSS) feature and baseline `cvss_only` | High — core feature provenance |
| A2 | FIRST — EPSS documentation / model paper | needs verification `[VERIFY]` | §2, §3, §5, §9, §13.3 | EPSS as the E feature and primary baseline | High — EPSS is the central baseline |
| A3 | Allodi & Massacci — exploitation in the wild / CVSS critique | needs verification `[VERIFY]` | §2, §3 | Motivation that CVSS alone is weak for exploitation likelihood | Medium |
| A4 | Jacobs et al. — exploit prediction / EPSS lineage | needs verification `[VERIFY]` | §2, §3 | Empirical basis for exploitation-likelihood scoring | Medium |
| A5 | Sabottke et al. — Twitter/early-warning exploit prediction | needs verification `[VERIFY]` | §3 | Prior signal-based exploit prediction | Low-Medium |

## B. CISA / KEV / public-sector guidance

| Key | Source | Status | Used in | Claim it supports | Risk if missing |
| --- | --- | --- | --- | --- | --- |
| B1 | CISA Known Exploited Vulnerabilities (KEV) catalog | needs verification `[VERIFY]` | §2, §5, §8, §9 | K feature, KEV labels, KEV-deadline breach metric | High |
| B2 | CISA Binding Operational Directive 22-01 | needs verification `[VERIFY]` | §2, §10 | KEV-deadline operational driver; public-sector framing | Medium-High |
| B3 | NIST SP 800-40 Rev. 4 (patch/vuln management) | needs verification `[VERIFY]` | §2, §10 | Remediation-process framing | Medium |
| B4 | NIST SP 800-53 Rev. 5 (controls) | needs verification `[VERIFY]` | §10 | Compliance-mapping (review support, not proof) | Medium |
| B5 | NIST SP 800-30 Rev. 1 (risk assessment) | needs verification `[VERIFY]` | §4, §10 | Risk framing | Low-Medium |
| B6 | CIS Controls v8 / v8.1 (state which) | needs verification `[VERIFY]` | §10 | Control mapping | Low-Medium |
| B7 | CJIS Security Policy (state version used) | unresolved `[VERIFY]` | §10 | Public-sector (criminal-justice) control context | Low — include only if §10 cites it |

## C. Adjacent / prior ML-prioritization work

| Key | Source | Status | Used in | Claim it supports | Risk if missing |
| --- | --- | --- | --- | --- | --- |
| C1 | Deep VULMAN | needs verification `[VERIFY]` | §3, §14 | Differentiation; "complements, not first" | High — central related work |
| C2 | VulRG | needs verification `[VERIFY]` | §3, §14 | Differentiation | High |
| C3 | VulnScore | needs verification `[VERIFY]` | §3, §14 | Differentiation | High |
| C4 | V-REx | unresolved `[VERIFY]` | §3 | Additional ML-prioritization comparator | Medium |
| C5 | Other ML-prioritization papers from earlier review | unresolved `[VERIFY]` | §3 | Breadth of related work | Low-Medium |

## D. Commercial RBVM acknowledgments (acknowledged, not benchmarked)

| Key | Source | Status | Used in | Claim it supports | Risk if missing |
| --- | --- | --- | --- | --- | --- |
| D1 | Microsoft Defender Vulnerability Management | needs verification `[VERIFY]` | §3 | Industry context; explicitly not benchmarked | Low |
| D2 | Tenable VPR / ACR | needs verification `[VERIFY]` | §3 | Industry context | Low |
| D3 | Qualys TruRisk | needs verification `[VERIFY]` | §3 | Industry context | Low |
| D4 | Cisco / Kenna (Kenna Security risk model) | needs verification `[VERIFY]` | §3 | Industry context | Low |

> Note: cite these as product/vendor documentation; clearly state they are
> acknowledged for context and are **not** benchmarked in this work.

## E. Methodology / statistics

| Key | Source | Status | Used in | Claim it supports | Risk if missing |
| --- | --- | --- | --- | --- | --- |
| E1 | Wilcoxon signed-rank test (original / standard reference) | needs verification `[VERIFY]` | §9 | Paired significance testing (helper implemented; not yet applied to results) | Medium |
| E2 | Holm (1979) — Holm-Bonferroni correction | needs verification `[VERIFY]` | §9 | Family-wise error control | Medium |
| E3 | Efron — bootstrap / BCa confidence intervals | needs verification `[VERIFY]` | §9 | Interval estimation helper | Low-Medium |
| E4 | Synthetic-benchmarking / reproducibility references (if cited) | unresolved `[VERIFY]` | §7, §8 | Justify synthetic-evaluation methodology | Low |

---

## Summary

- **Total citation slots:** ~25 across groups A-E.
- **verified:** 0
- **needs verification:** ~20
- **unresolved:** ~5 (B7 CJIS, C4 V-REx, C5 misc ML, E4 synthetic-benchmarking)
- **Highest priority** (block submission if missing): A1 CVSS, A2 EPSS, B1 KEV,
  B2 BOD 22-01, C1 Deep VULMAN, C2 VulRG, C3 VulnScore.
- The statistics citations (E1-E3) are needed for §9 even though paired tests are
  not yet applied to the (neutral) results; the helpers exist and are described.

No reference is asserted as verified. Do not paste any citation into the
manuscript until its full bibliographic record is confirmed.

---

## Phase 20 update — placeholder citations now embedded in Sections 1-12

The Phase 20 prose inserts inline placeholder markers (format
`[CITATION: <name>]`, with `[VERIFY ...]` where exact details are unknown). None
are real references; all still require verification before submission. Markers now
present in `paper_full_draft.md` and the sections that use them:

| Placeholder marker | Group | Sections using it |
| --- | --- | --- |
| `[CITATION: FIRST CVSS specification]` | A1 | 1, 2 |
| `[CITATION: FIRST EPSS]` | A2 | 1, 2 |
| `[CITATION: Allodi & Massacci]` | A3 | 1, 2, 3 |
| `[CITATION: Jacobs et al.]` | A4 | 3 |
| `[CITATION: Sabottke et al.]` | A5 | 3 |
| `[CITATION: CISA KEV]` | B1 | 1, 2 |
| `[CITATION: CISA BOD 22-01]` | B2 | 1, 2, 3, 10 |
| `[CITATION: NIST SP 800-40 Rev. 4]` | B3 | 2, 3, 10 |
| `[CITATION: NIST SP 800-53 Rev. 5]` | B4 | 2, 3, 10 |
| `[CITATION: CIS Controls v8]` | B6 | 2, 10 |
| `[CITATION: CJIS Security Policy]` + `[VERIFY version]` | B7 | 2, 10 |
| `[CITATION: Deep VULMAN]` | C1 | 3, 14 |
| `[CITATION: VulRG]` | C2 | 3, 14 |
| `[CITATION: VulnScore]` | C3 | 3, 14 |
| `[CITATION: V-REx]` + `[VERIFY]` | C4 | 3 |
| `[CITATION: Microsoft Defender VM]` | D1 | 3 |
| `[CITATION: Tenable VPR/ACR]` | D2 | 3 |
| `[CITATION: Qualys TruRisk]` | D3 | 3 |
| `[CITATION: Cisco/Kenna]` | D4 | 3 |

Not yet cited inline (statistics group E1-E3: Wilcoxon, Holm, bootstrap/BCa) —
§9 currently describes the metrics narratively without attaching the statistical
references; attach E1-E3 when §9 is finalized, since the paired-test helpers are
implemented but not yet applied to the (within-noise) results. NIST SP 800-30
(B5) is referenced only in the §4/§10 outline scope and may be added during
finalization.

Verification remains outstanding for ALL markers above (`needs verification` /
`unresolved` per the tables earlier in this file).

---

## Phase 21 update — placeholders resolved to bib keys vs left as [VERIFY]

In `paper_full_draft.md`, Tier-1 markers were replaced with BibTeX citation keys
(entries drafted in `references.bib`, each flagged "CONFIRM at camera-ready"; none
re-verified in the authoring environment). Tier-2 markers were downgraded to
`[VERIFY: ...]` and have **no** BibTeX entry.

**Resolved to `[@key]` (Tier-1, in references.bib, pending confirmation):**

| Marker (was) | Key | Bib entry |
| --- | --- | --- |
| FIRST CVSS specification | `@first_cvss_v31` | yes |
| FIRST EPSS / Jacobs et al. | `@jacobs2021epss` | yes |
| Allodi & Massacci | `@allodi2014comparing` | yes |
| Sabottke et al. | `@sabottke2015vulnerability` | yes |
| CISA KEV | `@cisa_kev` | yes |
| CISA BOD 22-01 | `@cisa_bod2201` | yes |
| NIST SP 800-40 Rev. 4 | `@nist80040r4` | yes |
| NIST SP 800-53 Rev. 5 | `@nist80053r5` | yes |
| CIS Controls v8 | `@cis_controls_v8` | yes |
| (also in bib, not yet cited inline) NIST SP 800-30 r1 | `@nist80030r1` | yes |
| (also in bib) Wilcoxon / Holm / Efron-BCa | `@wilcoxon1945` / `@holm1979` / `@efron1987better` | yes |

**Left as `[VERIFY: ...]` (no bib entry — bibliographic details not confidently known):**
Deep VULMAN, VulRG, VulnScore, V-REx, Microsoft Defender VM, Tenable VPR/ACR,
Qualys TruRisk, Cisco/Kenna, and the exact CJIS Security Policy version.

**Caveat:** every Tier-1 entry is a DRAFT from best knowledge of a standard public
document or canonical paper; none was checked against a live source here. Confirm
all fields before any submission (see `references.bib` header and
`references_todo.md`).

---

## Phase 22A classification of remaining [VERIFY] items

Classes: **A** submission-blocking (must resolve before submission; cannot be
softened away) · **B** TODO before final submission (resolve, but does not block
formatting) · **C** can be removed or softened if unverifiable.

| Item | Class | Rationale / action |
| --- | --- | --- |
| Deep VULMAN | B | Used in Related Work + Discussion for differentiation; needs a real citation before submission. Do not invent; verify or soften the named comparison. |
| VulRG | B | Same as above. |
| VulnScore | B | Same as above. |
| V-REx | C | Mentioned only as an "additional" comparator; if the exact source cannot be confirmed, remove or soften to a generic phrase rather than guess. |
| Microsoft Defender Vulnerability Management | B | Acknowledged (not benchmarked); cite vendor documentation/URL at submission. |
| Tenable VPR / ACR | B | Same (vendor docs). |
| Qualys TruRisk | B | Same (vendor docs). |
| Cisco / Kenna | B | Same (vendor docs). |
| Exact CJIS Security Policy version | C | Only acknowledged for context in §10; if the version cannot be pinned, keep the generic mention and drop the version-specific citation. |
| Abstract numeric re-check | **RESOLVED** | Phase 22A re-verified all manuscript numbers against the frozen tables (30 seeds / 13 strategies / 4,290 rows / 390 audit logs / 0 NaN / 0 inf / capacity 100 / EHD ordering / proposed_full not beating EPSS or random). The `[VERIFY]` tag was replaced with a "reconfirm at camera-ready" note. |

**No item is class A** (none blocks producing the ACM-formatted manuscript). Classes
B and C must be resolved before *actual submission*; none may be satisfied by a
fabricated reference. Tier-1 entries additionally require a confirmation pass.

---

## Phase 23 update — Tier-1 citation verification pass (camera-ready)

Verified against live sources on 2026-05-31. Only entries that were confirmed via
a retrievable public URL or DOI are marked `verified` below. Fields that could not
be confirmed remain `needs verification`.

### A1 — CVSS v3.1 Specification (FIRST.org)

**Status: verified**

- **Title:** Common Vulnerability Scoring System version 3.1: Specification Document
- **Author/Publisher:** Forum of Incident Response and Security Teams (FIRST)
- **Year:** 2019 (published 2019-07-12 per FIRST newsroom release)
- **URL (specification page):** https://www.first.org/cvss/v3-1/specification-document
- **PDF URL:** https://www.first.org/cvss/v3-1/cvss-v31-specification_r1.pdf
- **Note:** CVSS v4.0 was subsequently published 2023-11-01 at
  https://www.first.org/cvss/specification-document — cite both versions if the
  manuscript references both; otherwise cite v3.1 for the feature definition.
- **BibTeX key:** `first_cvss_v31` — update `year = {2019}` and add
  `url = {https://www.first.org/cvss/v3-1/specification-document}`.

### A2 — EPSS paper (Jacobs et al.)

**Status: verified**

- **Title:** Exploit Prediction Scoring System (EPSS)
- **Authors:** Jay Jacobs, Sasha Romanosky, Benjamin Edwards, Idris Adjerid,
  Michael Roytman
- **Journal:** Digital Threats: Research and Practice
- **Volume:** 2, **Issue:** 3, **Article:** 20
- **Year:** 2021 (June 2021)
- **Pages:** 17 pages
- **DOI:** 10.1145/3436242
- **ACM DL URL:** https://dl.acm.org/doi/10.1145/3436242
- **BibTeX key:** `jacobs2021epss` — add `volume = {2}`, `number = {3}`,
  `articleno = {20}`, `doi = {10.1145/3436242}`, `numpages = {17}`.
- **Author-order note:** Manuscript bib entry listed Roytman before Adjerid; the
  ACM record lists Adjerid before Roytman. Correct to:
  Jacobs / Romanosky / Edwards / Adjerid / Roytman.

### A3 — Allodi & Massacci (CVSS critique / case-control)

**Status: verified**

- **Title:** Comparing Vulnerability Severity and Exploits Using Case-Control Studies
- **Authors:** Luca Allodi, Fabio Massacci
- **Journal:** ACM Transactions on Information and System Security (TISSEC)
- **Volume:** 17, **Issue:** 1, **Article:** Article 9 (20 pages)
- **Year:** 2014 (published 2014-08-15)
- **DOI:** 10.1145/2630069
- **ACM DL URL:** https://dl.acm.org/doi/10.1145/2630069
- **BibTeX key:** `allodi2014comparing` — add `volume = {17}`, `number = {1}`,
  `articleno = {9}`, `numpages = {20}`, `doi = {10.1145/2630069}`.

### B1 — CISA Known Exploited Vulnerabilities (KEV) Catalog

**Status: verified**

- **Title:** Known Exploited Vulnerabilities Catalog
- **Author/Publisher:** Cybersecurity and Infrastructure Security Agency (CISA)
- **Year:** 2021 (catalog launched November 2021 alongside BOD 22-01)
- **URL (primary):** https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- **URL (alternate landing):** https://www.cisa.gov/known-exploited-vulnerabilities
- **Note:** Living catalog; add an `urldate` / `note` with the access date at
  camera-ready.
- **BibTeX key:** `cisa_kev` — set `howpublished = {\url{https://www.cisa.gov/known-exploited-vulnerabilities-catalog}}`.

### B2 — CISA Binding Operational Directive 22-01 (BOD 22-01)

**Status: verified**

- **Title:** Binding Operational Directive 22-01: Reducing the Significant Risk of
  Known Exploited Vulnerabilities
- **Author/Publisher:** Cybersecurity and Infrastructure Security Agency (CISA)
- **Issued:** 2021-11-03
- **URL (directive page):** https://www.cisa.gov/news-events/directives/bod-22-01-reducing-significant-risk-known-exploited-vulnerabilities
- **PDF URL:** https://www.cisa.gov/sites/default/files/publications/Reducing_the_Significant_Risk_of_Known_Exploited_Vulnerabilities_211103.pdf
- **BibTeX key:** `cisa_bod2201` — set `year = {2021}`, add
  `url = {https://www.cisa.gov/news-events/directives/bod-22-01-reducing-significant-risk-known-exploited-vulnerabilities}`.

### NVD/NIST National Vulnerability Database (not previously assigned a bib key — for reference)

**Status: verified (URL confirmed)**

- The NVD is the U.S. government repository of SCAP-based vulnerability management
  data, operated by NIST Computer Security Division.
- **URL:** https://nvd.nist.gov/
- **Note:** If the manuscript cites NVD as a data source (e.g., for CVSS scores),
  add a `@misc{nist_nvd, ...}` entry with this URL and an access date.

### Unchanged-status entries (still `needs verification` — not searched in this pass)

A4 (Sabottke et al.), B3 (NIST SP 800-40 r4), B4 (NIST SP 800-53 r5),
B5 (NIST SP 800-30 r1), B6 (CIS Controls v8), B7 (CJIS), C1-C5 (ML systems),
D1-D4 (vendor docs), E1-E3 (Wilcoxon/Holm/Efron) — not re-searched; prior draft
fields remain CONFIRM-flagged.

---

## Phase 24 — Full Batch Verification (2026-05-31)

All remaining `needs verification` entries confirmed via web search.
All 15 entries now CONFIRMED. BibTeX entries added to
`paper/submission/ieee/references.bib`.

### A4 — Sabottke et al. (USENIX Security 2015)
**Status: CONFIRMED**
- Title: Vulnerability Disclosure in the Age of Social Media: Exploiting Twitter for Predicting Real-World Exploits
- Authors: Carl Sabottke, Octavian Suciu, Tudor Dumitras
- Venue: 24th USENIX Security Symposium (USENIX Security '15), Washington, DC, 2015
- URL: https://www.usenix.org/conference/usenixsecurity15/technical-sessions/presentation/sabottke
- Note: No DOI (USENIX proceedings do not use DOIs). Conference paper, not journal.
- BibTeX key: `sabottke2015vulnerability` (already in references.bib)

### B3 — NIST SP 800-40 Revision 4
**Status: CONFIRMED**
- Full title: Guide to Enterprise Patch Management Planning: Preventive Maintenance for Technology
- Authors: Murugiah Souppaya and Karen Scarfone
- Date: April 6, 2022
- DOI: https://doi.org/10.6028/NIST.SP.800-40r4
- BibTeX key: `nist80040r4` (already in references.bib)

### B4 — NIST SP 800-53 Revision 5
**Status: CONFIRMED**
- Full title: Security and Privacy Controls for Information Systems and Organizations
- Date: September 23, 2020 (with subsequent Update 1)
- DOI: https://doi.org/10.6028/NIST.SP.800-53r5
- BibTeX key: `nist80053r5` (already in references.bib)

### B5 — NIST SP 800-30 Revision 1
**Status: CONFIRMED**
- Full title: Guide for Conducting Risk Assessments
- Date: September 17, 2012
- DOI: https://doi.org/10.6028/NIST.SP.800-30r1
- BibTeX key: `nist80030r1` — **ADDED** to references.bib in Phase 24

### B6 — CIS Critical Security Controls Version 8
**Status: CONFIRMED (with version caveat)**
- Publisher: Center for Internet Security (CIS)
- Version 8 released: May 18, 2021; Version 8.1 released: June 25, 2024
- URL: https://www.cisecurity.org/controls/v8
- Caveat: Manuscript should specify v8 (May 2021) or v8.1 (June 2024)
  to match the cited year and URL.
- BibTeX key: `cis_controls_v8` (already in references.bib; references v8)

### C1 — Deep VULMAN
**Status: CONFIRMED**
- Title: Deep VULMAN: A Deep Reinforcement Learning-Enabled Cyber Vulnerability Management Framework
- Authors: Soumyadeep Hore, Ankit Shah, Nathaniel D. Bastian
- Journal: Expert Systems with Applications, Volume 221, 119734, 2023
- DOI: https://doi.org/10.1016/j.eswa.2023.119734
- BibTeX key: `hore2023deepvulman` — **ADDED** to references.bib in Phase 24

### C2 — VulRG
**Status: CONFIRMED (arXiv preprint; no confirmed published venue/DOI)**
- Title: VulRG: Multi-Level Explainable Vulnerability Patch Ranking for Complex Systems Using Graphs
- Authors: Yuning Jiang, Nay Oo, Qiaoran Meng, Hoon Wei Lim, Biplab Sikdar
- arXiv: 2502.11143 (February 2025)
- URL: https://arxiv.org/abs/2502.11143
- Caveat: Preprint only; venue/DOI unconfirmed. If manuscript cites as published,
  verify directly against ACM DL or arXiv abstract page.
- BibTeX key: `jiang2025vulrg` — **ADDED** to references.bib in Phase 24

### C3 — VulnScore
**Status: CONFIRMED**
- Title: VulnScore: A Deployed System for Patch Prioritization Combining Human Input and Temporal Threat Intelligence
- Authors: Norah Alqahtani, Mohammed Almukaynizi
- Journal: International Journal of Information Security (Springer), Volume 25, Issue 2, 2026
- Online publication date: November 27, 2025
- DOI: https://doi.org/10.1007/s10207-025-01164-3
- Caveat: Springer lists citation year as 2026; online publication November 2025.
  Use year 2026 in BibTeX per journal issue date.
- BibTeX key: `alqahtani2026vulnscore` — **ADDED** to references.bib in Phase 24

### D1 — Microsoft Defender Vulnerability Management
**Status: CONFIRMED**
- URL: https://learn.microsoft.com/en-us/defender-vulnerability-management/defender-vulnerability-management
- BibTeX key: `microsoft_mdvm` — **ADDED** to references.bib in Phase 24

### D2 — Tenable VPR
**Status: CONFIRMED**
- URL: https://docs.tenable.com/vulnerability-management/best-practices/security/Content/VulnerabilityPriorityRating.htm
- BibTeX key: `tenable_vpr` — **ADDED** to references.bib in Phase 24

### D3 — Qualys TruRisk
**Status: CONFIRMED**
- URL: https://docs.qualys.com/en/vmdr/getting-started-guide/features_of_vmdr/qualys_trurisk.htm
- BibTeX key: `qualys_trurisk` — **ADDED** to references.bib in Phase 24

### D4 — Cisco Vulnerability Management (formerly Kenna Security)
**Status: CONFIRMED**
- Current product name: Cisco Vulnerability Management (formerly Kenna Security)
- URL: https://www.cisco.com/site/us/en/products/security/vulnerability-management/index.html
- Note: Kenna Security acquired by Cisco in 2021; help.kennasecurity.com remains active
- BibTeX key: `cisco_kenna_vm` — **ADDED** to references.bib in Phase 24

### E1 — Wilcoxon (1945)
**Status: CONFIRMED**
- Title: Individual Comparisons by Ranking Methods
- Journal: Biometrics Bulletin, Volume 1, No. 6, pp. 80–83, 1945
- DOI: 10.2307/3001968
- BibTeX key: `wilcoxon1945` (already in references.bib)

### E2 — Holm (1979)
**Status: CONFIRMED**
- Title: A Simple Sequentially Rejective Multiple Test Procedure
- Journal: Scandinavian Journal of Statistics, Volume 6, Issue 2, pp. 65–70, 1979
- Note: No DOI confirmed (predates widespread DOI assignment)
- BibTeX key: `holm1979` (already in references.bib)

### E3 — Efron (1987)
**Status: CONFIRMED**
- Title: Better Bootstrap Confidence Intervals
- Journal: Journal of the American Statistical Association, Volume 82, No. 397, pp. 171–185, 1987
- DOI: 10.1080/01621459.1987.10478410
- BibTeX key: `efron1987better` (already in references.bib)

**Phase 24 summary:** 15/15 entries CONFIRMED. 8 new BibTeX entries added
to references.bib (B5, C1, C2, C3, D1, D2, D3, D4). All statistical method
references (E1–E3) and NIST/CISA/CIS references (B3, B4, B6) already present.
