# The Drill Illusion: Latent Failover-Defect Decay and Continuous Chaos Testing

Code and frozen results for the paper. A disaster-recovery configuration silently rots between
periodic drills, so the probability that failover actually works decays even though the last drill
passed. A pre-registered simulation of twelve failover modes over a ten-year horizon quantifies the
gap and the recovery-confidence gain of continuous chaos testing.

## Headline result (25 pre-registered seeds, 1200 to 1224)

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1: continuous chaos raises at-random recovery by at least 0.10 | SUPPORTED | 0.688 to 0.949, gain 0.261, interval [0.255, 0.268] |
| H2: the gain is bounded by chaos-suite coverage | SUPPORTED | rises 0.218 to 0.291 across coverage; stays below the perfect-freshness ceiling |
| H3: the gain saturates as chaos cadence tightens | SUPPORTED | 0.165 to 0.231 to 0.261 to 0.270 across 90, 30, 7, 1 days |
| H4: the drill illusion grows with the drill interval | SUPPORTED | 0.313 annual to 0.202 to 0.119 to 0.044 monthly |

The message: a passing annual DR drill overstates real recovery confidence by 31 points, because the
drill measures the system at its single best moment. Continuous chaos testing closes most of the gap
at a weekly cadence, bounded by the failure-mode coverage of the chaos suite.

## Layout

```
design/PAPER18_PROTOCOL.md     Pre-registration (locked before any evaluation seed)
src/resilience/model.py        Latent-defect decay, validation schedules, recovery at random vs drill
src/run_evaluation.py          25 seeds, coverage / cadence / drill-interval sweeps
src/analyze.py                 Pre-registered hypothesis verdicts
src/make_figures.py            Figures 1 to 2
results/primary_v1/            Frozen result tables, run manifest, hypothesis summary
submission/ieee/               IEEE LaTeX source, references, figures
manuscript/paper18_draft_v0.1.md   Full manuscript
```

## Reproduce

```bash
pip install -r requirements.txt
cd src
python3 run_evaluation.py
python3 analyze.py
python3 make_figures.py
```

All randomness is seeded; `results/primary_v1/run_manifest.json` records the seeds, the defect-rate
mixture, the coverage and cadence sweeps, and the horizon.

## Data and integrity

No employer, operational, or recovery-test data is used. The failover modes, defect rates, coverage,
and cadence are synthetic with documented parameters. Model constants are fixed and not tuned on any
seed. Hypotheses, thresholds, and seeds were locked before any evaluation-seed result was inspected.
