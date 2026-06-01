# Paper 2 — EB1A Evidence Summary

**Purpose.** This file is the index for the Paper 2 EB1A evidence package. It
is an *internal* working document, not a submission, not a publication
artefact, not a recommendation letter. Nothing in this folder asserts that
Paper 2 has been peer-reviewed, accepted, externally cited, or used outside
this repository.

## What Paper 2 is

Paper 2 is a methodology paper with an honest negative result. It documents
the design, execution, and audit of a failure-aware multi-t0 calibration gate
for vulnerability prioritization using public exploit-signal feeds (NVD +
EPSS + KEV). The gate was triggered: only **7 unique positive CVEs** were
observed across **2,688 catalog-matched CVEs** and **18 monthly t0 windows**,
which is below the pre-registered minimum needed to fit defensible
per-feature weights. **Calibration was not attempted.** The paper reports
that fact and the failure-aware methodology that surfaced it.

Paper 2 is **not** a model-performance paper. It does not claim that any
prioritization strategy beats another. It is a sparse-label methodology
contribution.

## Index of files in this package

| File | Audience | Contents |
|---|---|---|
| `EB1A_EVIDENCE_SUMMARY.md` | author, attorney | this index |
| `USCIS_FRIENDLY_SUMMARY.md` | adjudicator-level reader | plain-English description of what was built and what it documents |
| `TECHNICAL_CONTRIBUTION_SUMMARY.md` | technical reviewer | the failure-aware gate design + the sensitivity framework |
| `ORIGINAL_CONTRIBUTION_STATEMENT.md` | attorney, recommender | what is new in Paper 2 relative to prior work |
| `FIELD_SIGNIFICANCE_STATEMENT.md` | attorney, recommender | why a failure-aware methodology matters to the vulnerability-prioritization research field |
| `RECOMMENDER_TALKING_POINTS.md` | letter-writer | honest, scoped talking points |
| `MEDIA_PITCH.md` | journalist (if used at all) | short, no-overclaim pitch |
| `LINKEDIN_POST.md` | author's personal channel | short descriptive post |
| `EXPERT_REVIEWER_OUTREACH.md` | invited reviewer | template for asking domain experts to read the methodology |
| `EXHIBIT_DESCRIPTION.md` | attorney | per-artefact descriptions of the technical exhibits this paper produces |
| `CLAIM_BOUNDARIES.md` | author, attorney, recommender | the explicit list of what may and may not be claimed about Paper 2 |

## Hard claim boundaries (apply to every file in this folder)

The following are **not** claimed anywhere in this package:

- the manuscript has been accepted, peer-reviewed, or externally cited;
- the work has been used, taken up, or installed outside the author's own
  repository;
- the methodology is a finished, ready-to-run, or government-endorsed
  artefact;
- any prioritization strategy beats EPSS or another comparator on this
  dataset;
- the calibration step succeeded.

The following **can** be honestly stated:

- the author built a reproducible methodology under a pre-registered design;
- the author produced public-feed sparse-label feasibility evidence;
- the author constructed a failure-aware calibration gate;
- the gate prevented a statistically unjustified calibration step from being
  performed;
- the author generated an audited primary run (1,440 seed-runs across 48
  cells, 8,640 metric rows, every row carrying a freeze-witness ID) and a
  submission scaffold;
- the author reported a negative result honestly, with claim and citation
  audits in place.

See `CLAIM_BOUNDARIES.md` for the enforceable wording rules.

## Key reproducibility quantities

- 7 unique positive CVEs across 18 monthly t0 windows.
- 2,688 catalog-matched CVEs (from a 31-product synthetic catalog against
  the normalized NVD universe).
- 48 primary cells × 30 seeds = 1,440 seed-runs; 8,640 metric rows total.
- Claim audit: 0 violations on the manuscript draft AND on the concatenated
  LaTeX section files.
- Citation audit: 15 verified BibTeX entries; 0 unresolved [VERIFY] markers.
- Paper 1 freeze invariant preserved (SHA-256 byte-equal before and after
  all Paper 2 batches).
- Submission scaffold produced under `paper2/submission/`. **No paper has
  been sent to any venue.**
