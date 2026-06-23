# CAP-G: Context-Aware Vulnerability Prioritization for Government Endpoint Fleets

Code and frozen results for the paper. CAP-G augments a hygiene-augmented exploit-likelihood
scorer with a pre-registered Asset Context Score (asset criticality tier, network exposure
zone, and data sensitivity, with category mixes drawn from FIPS 199, CISA BOD 22-01/23-01, and
the FBI CJIS Security Policy) and measures whether context-aware ranking improves mission
precision on a government fleet under a fixed remediation capacity.

## Headline result (25 pre-registered seeds, real EPSS/KEV corpus)

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1: MWP@K advantage at least 5 points averaged over K | PARTIAL | mean 4.4 points; +9.5 at K=50, +3.0 at K=100, +0.7 at K=250 (all intervals exclude 0) |
| H2: advantage decays with capacity | SUPPORTED | 9.5, 3.0, 0.7 points, monotone |
| H3: gain comes from fleet heterogeneity | SUPPORTED | homogeneous-fleet advantage 0.0, interval [0, 0] |
| H4: no cost-free generic-precision gain | SUPPORTED | context-blind P@50 difference +0.1 points, interval [-1.5, 1.6] |
| Ablation: which context dimension matters | criticality | -4.0 points MWP@50 when removed; zone and sensitivity add nothing |

CAP-G raises NDCG@50 from 0.339 to 0.613. It is a triage-regime tool: the benefit is large
where remediation capacity is scarce and negligible at high capacity.

## Layout

```
design/PAPER11_PROTOCOL.md     Pre-registration (locked before any evaluation seed)
src/capg/context.py            Asset Context Score and fleet context layer
src/capg/scorer.py             CAP-G scorer, hygiene-augmented base scorer, baselines
src/capg/metrics.py            Mission and context-blind targets, CWER, BCa intervals
src/capg/evaluate.py           Per-seed evaluation, all methods, rho calibration
src/hygieneprio/               Vendored EEHDA fleet generator and hygiene-risk scorer (self-contained)
data/cve_corpus_for_sampling.csv   Frozen real CVE corpus (203,174 rows) for EPSS/KEV resampling
src/run_evaluation.py          Calibrate rho, 25-seed evaluation, homogeneous control
src/analyze.py                 Pre-registered hypothesis verdicts -> hypothesis_summary.json
src/make_figures.py            Figures 1 to 4
results/primary_v1/            Frozen result tables, run manifest, hypothesis summary
submission/ieee/               IEEE LaTeX source, references, figures
manuscript/paper11_draft_v0.1.md   Full manuscript
```

## Reproduce

```bash
pip install -r requirements.txt
cd src
python3 run_evaluation.py   # calibrate rho, 25-seed evaluation, homogeneous control
python3 analyze.py          # hypothesis verdicts
python3 make_figures.py     # figures
```

All randomness is seeded; `results/primary_v1/run_manifest.json` records seeds (evaluation
200 to 224, calibration 11, 22, 33, 44, 55), rho, weights, and the corpus snapshot.

## Building the PDF

`submission/ieee/main.pdf` is a draft rendered from the manuscript. The submission-grade IEEE
two-column PDF compiles from the LaTeX source:

```bash
cd submission/ieee
tectonic main.tex          # or: xelatex main && bibtex main && xelatex main && xelatex main
```

## Data and integrity

No employer or operational data is used. Hosts, context attributes, and fleet structure are
synthetic with public structural priors; only each CVE's EPSS score and KEV membership are
real, resampled from a frozen FIRST EPSS and CISA KEV snapshot (2026-06-05, 203,174 CVEs).
Hypotheses, thresholds, metrics, and seeds were locked in the pre-registration before any
evaluation-seed result was inspected, and the partially-supported primary hypothesis is
reported as such rather than re-cut to a clean pass.
