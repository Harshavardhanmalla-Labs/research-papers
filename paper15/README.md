# Fusing Real-Time and Scheduled Endpoint Telemetry for Vulnerability Visibility

Code and frozen results for the paper. How much does fusing a real-time endpoint feed (fresh,
partial coverage) with a scheduled feed (stale, different partial coverage) improve
current-vulnerability visibility over the better single tool, and what bounds it? A pre-registered
simulation of a 5,000-asset fleet, sweeping the coverage overlap between the two tools.

## Headline result (25 pre-registered seeds, 1000 to 1024)

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1: fusion beats the better single tool by at least 0.10 recall | SUPPORTED | 0.870 vs 0.750, gain 0.120, interval [0.117, 0.123] |
| H2: the blind spot is a hard floor on missed vulnerabilities | SUPPORTED | 5.1% blind spot floor + 7.9% stale-scheduled residual |
| H3: the gain equals the scheduled-only fresh coverage | SUPPORTED | gain over real-time 0.120 = scheduled-only-fresh 0.120 (difference 0.000) |
| H4: the gain shrinks as tool overlap grows | SUPPORTED | 0.149 to 0.000 across the overlap sweep, while the blind spot grows 0 to 25% |

The message: fusion's entire value is the complementary coverage one tool has and the other lacks;
where the tools overlap, fusion adds nothing, and where neither reaches, it cannot help. Pair
complementary tools and spend visibility effort on closing the blind spot.

## Layout

```
design/PAPER15_PROTOCOL.md     Pre-registration (locked before any evaluation seed)
src/fusion/model.py            Coverage classes, freshness, three regimes, recall
src/run_evaluation.py          25 seeds x 5 overlap levels
src/analyze.py                 Pre-registered hypothesis verdicts
src/make_figures.py            Figures 1 to 2
results/primary_v1/            Frozen result tables, run manifest, hypothesis summary
submission/ieee/               IEEE LaTeX source, references, figures
manuscript/paper15_draft_v0.1.md   Full manuscript
```

## Reproduce

```bash
pip install -r requirements.txt
cd src
python3 run_evaluation.py
python3 analyze.py
python3 make_figures.py
```

All randomness is seeded; `results/primary_v1/run_manifest.json` records the seeds, the coverage and
freshness probabilities, and the overlap sweep.

## Data and integrity

No employer, operational, or telemetry data is used. The fleet and its coverage, overlap, and
freshness probabilities are synthetic with documented priors. Model constants are fixed and not
tuned on any seed. Hypotheses, thresholds, and seeds were locked before any evaluation-seed result
was inspected.
