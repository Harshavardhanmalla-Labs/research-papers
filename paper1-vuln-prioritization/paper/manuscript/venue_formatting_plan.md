# Venue Formatting Plan

This is a **reproducible benchmark / framework paper with a neutral empirical
result** (the proposed model does not beat EPSS or random under toy fixtures +
placeholder weights). Venue fit must tolerate a negative/neutral finding and value
reproducibility and artifact quality over a headline improvement.

## Candidate venues

### 1. ACM Digital Threats: Research and Practice (DTRAP) — RECOMMENDED PRIMARY
- **Why suitable:** explicitly welcomes reproducible, practice-oriented security
  research, datasets/benchmarks, and negative/neutral results; EPSS itself was
  published here, so the framing and baselines are in-scope.
- **Formatting requirement:** ACM `acmart` LaTeX template (journal/`acmsmall`
  variant); ACM reference format; ORCID and CCS concepts typically required.
- **Likely risk:** reviewers may ask for calibrated weights and at least one
  robustness cut before acceptance; artifact-evaluation expectations are high
  (which this work is built to meet).
- **Neutral-benchmark fit:** strong — DTRAP values reproducible methodology and is
  receptive to "context did not help without calibration" framed as a benchmark.
- **Next formatting step:** port `paper_submission_draft.md` into `acmart`; compile
  `references.bib` (confirm Tier-1 fields; resolve `[VERIFY]` works or drop them);
  prepare an artifact-evaluation appendix from `reproducibility_appendix.md`.

### 2. Computers & Security (Elsevier)
- **Why suitable:** broad operational-security scope; accepts framework/benchmark
  contributions and public-sector security-operations topics.
- **Formatting requirement:** Elsevier `elsarticle` LaTeX; structured abstract and
  highlights; numbered Elsevier reference style.
- **Likely risk:** reviewers may expect a positive empirical contribution or
  real-data validation; the neutral result needs careful framing as a benchmark
  contribution; review cycles can be long.
- **Neutral-benchmark fit:** moderate — acceptable if the benchmark/framework
  contribution is foregrounded over the comparison.
- **Next formatting step:** `elsarticle` port, structured abstract + highlights,
  reference-style conversion.

### 3. IEEE Access
- **Why suitable:** multidisciplinary, accepts reproducibility/benchmark and
  systems papers; fast, open-access; tolerant of incremental/neutral results when
  rigor and reproducibility are clear.
- **Formatting requirement:** IEEE Access LaTeX template; IEEE reference style;
  open-access article-processing charge applies.
- **Likely risk:** lower selectivity may weaken prestige signal; still requires
  clean citations and figures.
- **Neutral-benchmark fit:** good — explicitly accepts negative/neutral results
  with sound methodology.
- **Next formatting step:** IEEE Access template port; IEEE reference conversion.

## Recommendation

**Primary target: ACM DTRAP.** Best alignment for a reproducible,
audit-evidence-producing benchmark with honest neutral findings, with EPSS-adjacent
framing in-scope. **Fallback: IEEE Access** (fast, tolerant of neutral results),
then **Computers & Security**.

**Pre-submission gating regardless of venue:** (a) confirm all Tier-1 citations and
resolve or remove `[VERIFY]` works; (b) decide the calibrated-weights question — a
calibrated rerun likely strengthens any venue outcome, though the paper is
submittable as a benchmark/feasibility contribution without it; (c) apply the
venue template and finalize Table/Figure placement.
