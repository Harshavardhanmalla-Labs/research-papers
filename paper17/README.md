# Ring Rollout of Script-Based Endpoint Enforcement: Bounding the Blast Radius

Code and frozen results for the paper. How much does a ring (canary) rollout of an enforcement
script reduce the blast radius of a faulty policy, and what does it cost? A pre-registered Monte
Carlo simulation of a 10,000-endpoint fleet, sweeping rollout granularity and canary detection
probability.

## Headline result (25 pre-registered seeds, 1100 to 1124)

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1: four-ring rollout cuts expected blast radius by at least 80% vs big-bang | SUPPORTED | 95.2% reduction (1.0 to 0.048), interval [95.1, 95.3] |
| H2: convergence cost equals the number of inter-ring stages | SUPPORTED | 0, 1, 3, 5 soak periods for big-bang, two-, four-, six-ring |
| H3: containment scales with canary observability | SUPPORTED | blast radius 0.016 to 0.594 as detection probability falls 0.95 to 0.20 |
| H4: finer staging reduces blast radius with diminishing returns | SUPPORTED | 0.239 to 0.048 to 0.013; marginal reductions 76, 19, 4 points |

The message: small early rings bound the blast radius cheaply, but the containment only works if the
canary detects the fault, and finer staging buys little extra at a constant soak cost. Stage with
small early rings, invest in canary observability first, and stop adding rings at the sweet spot.

## Layout

```
design/PAPER17_PROTOCOL.md     Pre-registration (locked before any evaluation seed)
src/rollout/model.py           Ring rollout, fault detection, Monte Carlo blast radius
src/run_evaluation.py          25 seeds, config + detection sweeps
src/analyze.py                 Pre-registered hypothesis verdicts
src/make_figures.py            Figures 1 to 2
results/primary_v1/            Frozen result tables, run manifest, hypothesis summary
submission/ieee/               IEEE LaTeX source, references, figures
manuscript/paper17_draft_v0.1.md   Full manuscript
```

## Reproduce

```bash
pip install -r requirements.txt
cd src
python3 run_evaluation.py
python3 analyze.py
python3 make_figures.py
```

All randomness is seeded; `results/primary_v1/run_manifest.json` records the seeds, the fault rate,
the ring configurations, the detection-probability sweep, and the Monte Carlo trial count.

## Data and integrity

No employer, operational, or deployment data is used. The fault rate, ring fractions, and detection
probability are synthetic with documented parameters. Model constants are fixed and not tuned on any
seed. Hypotheses, thresholds, and seeds were locked before any evaluation-seed result was inspected.
