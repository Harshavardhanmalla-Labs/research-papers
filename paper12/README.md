# NIST 800-53 as Code: Continuous Automated Evidence Collection and Its Automatability Ceiling

Code and frozen results for the paper. How much does continuous automated evidence collection
(compliance as code) reduce compliance exposure relative to periodic manual assessment, and what
bounds that reduction? A pre-registered simulation of a 200-control catalog drifting out of
compliance as a Poisson process over two years.

## Headline result (25 pre-registered seeds, 800 to 824)

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1: continuous cuts MTTD on automatable controls by at least 10x | SUPPORTED | 272 days to 1 day, a factor of 272, interval [269, 275] |
| H2: overall exposure reduction is capped by the automatable share | SUPPORTED | reduction 0.567 vs ceiling 0.643; the reduction stays below the ceiling |
| H3: diminishing returns as the manual cadence tightens | SUPPORTED | 33,000 control-days saved over annual vs 16,000 over quarterly |
| H4: the value concentrates in high-drift controls | SUPPORTED | the top-drift quartile captures 79% of the achievable reduction |

The message: continuous compliance as code cuts detection latency on automatable controls from
about nine months to one day, but the un-automatable controls form a floor that caps the overall
exposure reduction at the automatable share, and the value concentrates in high-drift controls.
Instrument the high-drift automatable controls first.

## Layout

```
design/PAPER12_PROTOCOL.md     Pre-registration (locked before any evaluation seed)
src/compliance/model.py        Control catalog, drift process, periodic and continuous regimes
src/run_evaluation.py          25 seeds
src/analyze.py                 Pre-registered hypothesis verdicts
src/make_figures.py            Figures 1 to 2
results/primary_v1/            Frozen result tables, run manifest, hypothesis summary
submission/ieee/               IEEE LaTeX source, references, figures
manuscript/paper12_draft_v0.1.md   Full manuscript
```

## Reproduce

```bash
pip install -r requirements.txt
cd src
python3 run_evaluation.py
python3 analyze.py
python3 make_figures.py
```

All randomness is seeded; `results/primary_v1/run_manifest.json` records the seeds, the drift and
automatability distributions, the horizon, and the cadences.

## Data and integrity

No employer, operational, or audit data is used. The control catalog and its drift and
automatability distributions are synthetic with documented priors. Model constants are fixed and
not tuned on any seed. Hypotheses, thresholds, and seeds were locked before any evaluation-seed
result was inspected.
