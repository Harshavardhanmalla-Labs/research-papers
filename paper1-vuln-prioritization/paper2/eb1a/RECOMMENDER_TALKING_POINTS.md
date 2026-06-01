# Paper 2 — Recommender Talking Points

This file is a set of honest, scoped bullets a letter-writer may draw from
when describing the author's Paper 2 work. It is **not** a letter, and it
asserts nothing about peer-review, acceptance, citation, or outside use.
A recommender should write in their own voice and may decline any bullet
they do not personally believe.

## Talking point set A — what the author did

- The author designed, ran, and audited a methodology study on whether
  public exploit-signal feeds (NVD + EPSS + KEV) are dense enough to
  support per-feature weight fitting for vulnerability prioritization.
- The author committed to a pre-registered design before collecting any
  data: weight families, stop rules, inference policy, cell enumeration,
  freeze invariant, and compute budget were locked in nine fix documents
  (F1–F9) and then implemented as machine-readable artefacts.
- The author built a failure-aware multi-time-origin calibration gate that
  refuses to fit weights when the number of unique positive CVEs across
  windows is below a pre-registered minimum.
- The author ran the gate on the actual data: 7 unique positive CVEs across
  18 monthly time-origin windows and 2,688 catalog-matched CVEs. The gate
  fired and calibration was not attempted.
- The author then executed a 48-cell fixed-prior sensitivity sweep (1,440
  seed-runs, 8,640 metric rows), with every row carrying a freeze-witness
  identifier tying it back to a prior frozen artefact.
- The author reported the negative result honestly, with claim-audit and
  citation-audit reports attached.

## Talking point set B — what the author chose not to do

- The author chose not to fit per-feature weights despite having the
  machinery to do so, because the pre-registered K1 stop rule said the
  label density was too low.
- The author chose not to claim that any prioritization strategy beats
  another on this dataset, because the K8 stop rule fired on every measured
  sensitivity axis and required demoting those axes to descriptive only.
- The author chose not to claim catalog stability under product
  perturbations, because the K7 perturbation data was not generated, and
  the manuscript records that as a limitation.

## Talking point set C — discipline and reproducibility

- Every numeric quantity in the manuscript traces to a JSON field or CSV
  cell in the repository, mapped row-by-row in
  `paper2/submission/REPRODUCIBILITY_APPENDIX.md`.
- A claim-audit script scans the manuscript for an enumerated set of
  overclaim phrases (with proximity rules and a negation window) and
  reports zero violations on the current draft.
- A citation-audit report lists 15 verified BibTeX entries, zero unresolved
  `[VERIFY]` markers, and four routine pre-submission human-review chores.
- A freeze-invariant contract requires the Paper 1 SHA-256 manifest to be
  byte-equal before and after every Paper 2 batch; the manuscript records
  that contract as having held throughout.

## Talking point set D — what may NOT be said in a letter

A recommender writing for the author should avoid the following:

- That the paper has been peer-reviewed, accepted, or published.
- That the methodology has been used or installed anywhere outside this
  repository.
- That the work has been cited, taken up, or endorsed by any organization.
- That the methodology is a finished or ready-to-run artefact.
- That any prioritization strategy is "better" or "best" on this dataset.
- That the calibration step succeeded.
- That a "learned model" exists in this study (none was fit).

If a recommender is unsure whether a phrase crosses one of these lines,
the safer choice is to substitute a description of *what the author did*
for a description of *what the work has achieved externally*.

## Talking point set E — short paragraph the recommender may adapt

"In Paper 2 the author addressed a question that the vulnerability-
prioritization research community has rarely asked directly: are public
exploit-signal feeds dense enough, under a leakage-safe label, to support
the per-feature weight fitting that recent work routinely performs? The
author built a failure-aware multi-time-origin gate that operationalizes
that question as a pre-registered stop rule, ran the gate on a 31-product
synthetic catalog across 18 monthly time origins, observed only 7 unique
positive CVEs out of 2,688 catalog-matched CVEs, and honestly reported that
weight fitting was therefore not attempted. The remainder of the study is
a 48-cell fixed-prior sensitivity sweep whose axes the author demotes to
descriptive only on the basis of a pre-registered noise-versus-signal
criterion. The work is, in my view, an example of careful methodology and
of negative-result discipline."

A recommender may use the above paragraph as a starting point, rewrite it
in their own voice, or decline to use it. It should not be quoted as
having been said by anyone other than the recommender themselves.
