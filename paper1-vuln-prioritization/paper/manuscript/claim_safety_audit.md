# Claim-Safety Audit (Phase 19)

Scope: all manuscript prose currently in the repository — i.e. the Phase 18 draft
(`paper/draft_results_discussion.md`, inlined into `paper_full_draft.md` as
Sections 13-17 + Abstract). Sections 1-12 are placeholders (no prose yet); their
required safe positions are listed at the end so the language is correct when the
earlier-drafted prose is pasted in.

Method: scanned for `outperform`, `superior`, `autonomous`, `AI-driven`,
`audit-ready`, `proves`, `guarantees`, `real-world`, `validated`,
`compliance achieved`, `first ever`, `state-of-the-art`.

## Findings in existing prose (Sections 13-17 + Abstract)

| # | Original phrase (context) | Term | Risk | Verdict / action |
| --- | --- | --- | --- | --- |
| 1 | "we do not draw any ranking-quality **superiority** claim for the proposed model" | superior | none — explicitly negated | **Keep** |
| 2 | "do **not** establish **real-world** **superiority** of any strategy" | real-world, superior | none — negated | **Keep** |
| 3 | "do **not** show that proposed_full beats EPSS or random" | (beats) | none — negated | **Keep** |
| 4 | "do **not** demonstrate **autonomous** remediation (the scheduler simulates approval and timing, not patch execution)" | autonomous | none — negated + clarified | **Keep** |
| 5 | "do **not** **prove** **compliance**" | proves, compliance | none — negated | **Keep** |
| 6 | "not a new **state-of-the-art** score" | state-of-the-art | none — negated | **Keep** |
| 7 | "**Audit evidence is not compliance.**" | compliance | none — explicit disclaimer | **Keep** |
| 8 | "no ... real-world exploitation outcomes were used to **validate** predictions" | validate | none — describes absence | **Keep** |
| 9 | "**validates** the artifact's inspection, scheduling, and append-only audit pipeline" | validated | low — refers to *software-artifact* validation, not field validation | **Keep** (acceptable; could soften to "exercises and checks" if a reviewer objects) |
| 10 | "**validates** artifact integrity end to end" (Conclusion) | validated | low — artifact integrity, not real-world | **Keep** |
| 11 | "externally **validated** prioritization studies can be built" (Abstract) | validated | none — future external validation | **Keep** |
| 12 | "does not **outperform** a random ordering" (Conclusion) | outperform | none — negated | **Keep** |
| 13 | Section heading "13.1 Experimental Integrity and Artifact **Validation**" | validation | low — artifact validation | **Keep** |

**Result:** every risky term in the existing prose is either negated or used in
the narrow, accurate sense of *software-artifact* validation/integrity. No
overclaiming present. No patch required to current prose. Recommend a single
optional softening of #9/#10 wording from "validates" to "exercises and checks"
if the target venue is sensitive to the word "validate."

## Required safe positions for Sections 1-12 (apply when pasting earlier prose)

| Unsafe formulation to avoid | Required safe replacement |
| --- | --- |
| "audit-ready" | "**audit-evidence-producing**" |
| "government infrastructure validation" / "validated in/on government infrastructure" | "**public-sector-shaped synthetic fleet**" (evaluation), not field validation |
| "outperforms EPSS" / "beats EPSS" | "**evaluated against EPSS**" (and report the neutral result honestly) |
| "proves compliance" / "compliance achieved" | "**supports compliance review**" |
| "autonomous remediation" | "**capacity-constrained scheduling simulation** with human-approval gates" |
| "AI-driven" (loose) | name the actual method: "linear / regularized-logistic scoring" (use "AI/ML" only when precisely tied to the calibrated model) |
| "first ever" / "novel first" | "**complements** prior work (Deep VULMAN, VulRG, VulnScore)"; do not claim first |
| "state-of-the-art" | omit; describe the contribution as reproducible benchmark infrastructure |
| "guarantees" / "proves" (effectiveness) | "**provides a falsifiable basis to test whether** …" |
| Any Introduction sentence implying expected empirical superiority | reframe as an **open research question** ("we ask whether …; we do not assume it does") |

## Phase 20 update — Sections 1-12 prose inserted

Sections 1-12 were reconstructed as full prose (Phase 20) and scanned with the
same 12-term list. Findings: every occurrence of a risky term is one of
(a) explicitly negated, (b) an explicit disclaimer listing forbidden words,
(c) a description of *prior work* (e.g. "weak predictor of real-world
exploitation [CITATION: Allodi & Massacci]"), (d) the standard statistical term
"cross-validation", or (e) the narrow *software-artifact* validation/integrity
sense. The Phase 20 prose was written directly against the required safe
positions, so **no patch was needed**. Representative safe usages:

| Section | Phrase | Term | Verdict |
| --- | --- | --- | --- |
| 1, 4, 12 | "we do not perform autonomous patching"; "(not autonomous remediation)" | autonomous | negated/clarified |
| 1, 12 | "does not outperform a random ordering"; "not a claim of a superior ... model" | outperform, superior | negated |
| 4, 10, 12 | "we do not claim that the framework guarantees or proves compliance — it produces evidence that supports review"; "Audit evidence is necessary for, but not equivalent to, compliance" | proves, guarantees, compliance | negated/disclaimer |
| 1, 3, 12 | "we do not claim to be first"; "complements prior work" | first ever | negated |
| 3 | "their models are closed ... incompatible with the reproducibility goal" (commercial RBVM not benchmarked) | — | safe framing |
| 8, 2 | "public-sector-shaped synthetic fleet"; explicit external-validity bounding | real-world/validated | safe |
| 12 | "audit-evidence-producing decision records" (never "audit-ready") | audit-ready | required term used |
| 7 | "time-block cross-validation" | validat* | statistical term, safe |

Result: Sections 1-12 are claim-safe; the manuscript-wide scan shows no
unguarded risky claim.

## Phase 21 update — extended scan (incl. "government infrastructure", "production")

Re-scanned `paper_full_draft.md` with the extended 14-term list. Results:

- **"government infrastructure"**: 0 occurrences. (The string "Government Endpoint
  Fleets" appears only in the paper *title*, and "government agencies" is used
  descriptively in Section 1 — neither is a validation claim.)
- **"production"**: 6 occurrences, all safe — "without exposing production data",
  "we do not perform production validation", "no production data is used", "No real
  production validation" (limitation), "do not constitute production validation",
  and "calibrated, production-scale studies" (future work). None claims production
  validation.
- All other terms (`outperform`, `superior`, `autonomous`, `proves`, `guarantees`,
  `real-world`, `validated`, `compliance`, `first ever`, `state-of-the-art`)
  remain negated, disclaimers, prior-work descriptions, "cross-validation", or the
  artifact-validation sense, exactly as in the Phase 20 audit.

**Verdict: manuscript-wide claim safety is clean; no unsafe phrase remains and no
rewrite was required in Phase 21.**

## Cross-check against the neutral result

The manuscript's central empirical statement is that, under toy fixtures and
placeholder weights, the proposed model is **statistically indistinguishable from
EPSS and does not beat random**. Sections 13.2, 13.3, 13.7, Discussion, and the
Abstract all state this plainly. No section asserts the opposite. Negative/neutral
findings are not hidden. ✅
