# Paper 2 — Submission Package (Step 11)

**Working title:** *When Calibration Fails: A Failure-Aware Public-Feed Gate
for Vulnerability Prioritization Under Sparse Exploit Labels*

**Status:** Packaging complete. **NOT submitted.** No paper has been sent to
any venue. This package is the artifact bundle a future submission would draw
from; submission itself is held until the venue template is locked and the
remaining items in §"Remaining blockers" are resolved by a human reviewer.

## Package contents

```
paper2/submission/
├── README.md                          (this file)
├── REPRODUCIBILITY_APPENDIX.md        per-claim numeric source map
├── CLAIM_AUDIT_REPORT.md              audit invocations + verdict (PASS)
├── CITATION_AUDIT_REPORT.md           citation re-verification + verdict
└── cset/                              LaTeX scaffold for USENIX CSET (primary)
    ├── README.md                      template status + compile notes
    ├── main.tex                       entry point
    ├── references.bib                 15 verified BibTeX entries
    ├── sections/                      16 .tex section files
    │                                  (00_abstract..15_reproducibility)
    ├── figures/                       14 figures (7 PNG + 7 PDF)
    └── tables/                        33 table files
        └── inference/                 12 inference-family tables
```

## Target venue and backups

| Role | Venue | Notes |
|---|---|---|
| Primary | USENIX **CSET** (Cyber Security Experimentation and Test) | Selected at F9. The CSET CFP / `.cls` / `.sty` must be re-verified at submission time. The current scaffold is template-agnostic with a `[VERIFY with current CSET CFP/template]` marker in `cset/main.tex`. |
| Backup 1 | **LASER** Workshop (Workshop on Learning from Authoritative Security Experiment Results) | Suitable for a negative-result methodology paper. |
| Backup 2 | ACM **DTRAP** (Digital Threats: Research and Practice) | Journal venue; longer-form discussion of methodology and limitations. |

A submission decision (which of these three to actually submit to) is **not**
made by this package. The packaging only ensures the artifacts are ready for
whichever venue a human reviewer ultimately picks.

## Remaining blockers before any submission can happen

1. **Venue-specific template substitution.** The `cset/main.tex` scaffold uses
   a neutral `\documentclass{article}` preamble. Before submission to CSET,
   the current CSET template must be downloaded, the document class swapped
   in, and the section files reviewed for any template-specific environment
   conflicts. (The section files only use `\section`, `\subsection`,
   `\subsubsection`, `itemize`, `\textbf`, `\emph`, `\texttt`, `\&`-style
   escapes, and `\input{figures/...}`-free figure references, so the
   substitution surface is small.)
2. **Author/affiliation block.** The scaffold uses `\author{Anonymous
   (submission scaffold)}`. CSET is double-blind for some review rounds;
   confirm submission-time anonymization requirements and add the final
   author block / acknowledgements only when the venue and round require it.
3. **Two placeholder author lists in `references.bib`** (VulRG, VMChaining) —
   replace `{VulRG authors}` and `{Vulnerability Management Chaining authors}`
   with the arXiv-confirmed author lists. See
   `CITATION_AUDIT_REPORT.md` §"Items requiring human review before
   submission" for the full list of pre-submission citation chores.
4. **LaTeX compile pass.** No LaTeX engine was invoked in Step 11 (the
   environment does not provide a guaranteed `pdflatex` toolchain). A human
   reviewer must run `pdflatex main.tex` (or equivalent) at submission time
   and resolve any environment-specific errors. See `cset/README.md` for the
   compile recipe.

## Compile instructions

From `paper2/submission/cset/`:

```
pdflatex main.tex
bibtex   main
pdflatex main.tex
pdflatex main.tex
```

The figures are provided in both `.png` and `.pdf` form; LaTeX should pick the
`.pdf` form by default when `graphicx` is used with the default extension
search order.

## What this paper does NOT claim

The negative-result discipline of Paper 2 forbids the following claims, none
of which appear in the manuscript or this package:

- **Calibration was performed.** It was not. The calibration stage was
  declared infeasible by K1 (7 unique positive CVEs across 18 t0 windows is
  below the pre-registered minimum of 50). All 48 cells are fixed-prior.
- **Any prioritization strategy outperforms EPSS.** No such claim is made.
  The K8 stop rule fires on every measured axis (within-cell seed noise
  exceeds across-cell signal), so the across-cell deltas are descriptive
  only.
- **The pipeline is validated, production-ready, or deployed.** None of
  these words appear in positive sense. The paper is an experimental
  methodology study on synthetic fleets + public feeds, not a deployment
  artifact.
- **The K7 catalog stability question is settled.** It is not; K7 was
  SKIPPED because no perturbation data was generated. This is recorded as a
  limitation.
- **Any improvement over Paper 1.** Paper 1 frozen outputs were not modified
  and are not compared to in a "better/worse" sense; the freeze SHA is
  verified as a witness on every metric row, no more.

See `CLAIM_AUDIT_REPORT.md` for the audit script's enforcement scope.

## Verification

To re-verify the package without re-running the pre-registered pipeline:

```
# Claim audit (manuscript markdown + concatenated LaTeX sections)
python3 scripts/paper2_claim_audit.py paper2/manuscript/paper2_full_draft.md
cat paper2/submission/cset/sections/*.tex > /tmp/paper2_concat.tex
python3 scripts/paper2_claim_audit.py /tmp/paper2_concat.tex

# Paper 1 freeze invariant
python3 -c "import json; d=json.load(open('paper/report/report_manifest.json')); \
  assert d['freeze_manifest_sha']=='750e144ba9567b5255b27ce40279643bdf7418d53b15edce5d72c515eb022833'; \
  print('Paper 1 freeze OK')"

# Primary completion status
python3 -c "import json; d=json.load(open('paper2/audit/primary_complete.json')); \
  assert d['status']=='PRIMARY_COMPLETE_VALID'; print('Primary OK')"
```

Both claim audits exit with code 0 (0 violations).
