# Paper 1 — Blockers (before submission)

Ordered by priority. None of these may be resolved by fabricating content.

## 1. Citation verification (HIGH)

- **Tier-1 (drafted in `references.bib`, flagged "CONFIRM"):** confirm every field
  (authors, year, venue, volume/issue, pages, DOI/URL) against the publisher of
  record — CVSS, EPSS/Jacobs, Allodi & Massacci, Sabottke, CISA KEV, BOD 22-01,
  NIST SP 800-40r4/800-53r5/800-30r1, CIS Controls v8, Wilcoxon, Holm, Efron. None
  was verified in the authoring environment.
- **Unresolved `[VERIFY]` (no bib entry; do not invent):**
  - Class B (resolve before submission): Deep VULMAN, VulRG, VulnScore, Microsoft
    Defender VM, Tenable VPR/ACR, Qualys TruRisk, Cisco/Kenna.
  - Class C (resolve or soften/remove): V-REx, exact CJIS Security Policy version.
  - In-text count: ~10 markers in `paper_submission_draft.md` /
    `paper/acm/sections/*.tex` (rendered as `\textbf{[VERIFY: ...]}`).

## 2. ACM template compile status (HIGH)

- The `paper/acm/` scaffold was **not compiled** — no TeX toolchain (`pdflatex`,
  `latexmk`, `acmart.cls`) in the authoring environment.
- TODO: compile with a TeX distribution; fix wide-table overflow (`\resizebox` /
  `booktabs` / landscape); add `\ccsdesc`, `\setcopyright`, venue metadata;
  optionally convert literal "Table N"/"Figure N" to `\ref{}`.

## 3. Calibrated-weight decision (MEDIUM — scientific)

- The frozen result uses **placeholder (uncalibrated) weights**; the proposed model
  does not separate from EPSS/random. Decide explicitly:
  - (a) submit as a benchmark/feasibility paper with the neutral result (current
    framing supports this), or
  - (b) run a calibrated-weights cell (the calibration code exists) and a new
    frozen artifact before submission. This would require a controlled run + freeze
    + inspection + regenerated tables/figures (a new phase), and must not modify the
    existing `results/primary_full_v1/` freeze.
- Related: decide whether to apply the implemented paired statistical tests / CIs
  or keep the descriptive-only framing (differences are within noise).

## 4. Final author metadata (LOW)

- Country, contact email, ORCID for the ACM front matter.

## Non-blockers (already satisfied)

- Manuscript structurally complete; numbers re-verified against the frozen
  artifact; claim-safety clean (extended 14-term scan); freeze verified; no
  EB1A/USCIS language in the paper; no confidential/production data.
