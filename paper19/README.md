# The Two-Sided Cost of CMDB Error: Ghost Assets, Phantom Assets, and Self-Healing Reconciliation

Code and frozen results for the paper. A configuration management database drifts from reality as
the fleet churns, producing ghost assets (real assets missing, a security cost) and phantom assets
(records with no real asset, a financial cost). A pre-registered Monte Carlo simulation of a
churning fleet quantifies both errors and the value and limits of continuous self-healing
reconciliation.

## Headline result (25 pre-registered seeds, 1300 to 1324)

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1: continuous reconciliation cuts total error by at least 30% vs quarterly | SUPPORTED | 0.605 to 0.134, a 77.8% reduction, interval [77.6, 78.0] |
| H2: retirement aggressiveness trades ghosts for phantoms | SUPPORTED | phantom 0.370 to 0.060, ghost 0.008 to 0.103 across the sweep; interior optimum at 14 days |
| H3: matching precision sets the accuracy floor | SUPPORTED | total error 0.283 to 0.095 as precision rises 0.80 to 0.99 |
| H4: the optimal retirement threshold follows the cost balance | SUPPORTED | 30 days (security-weighted), 14 (balanced), 7 (cost-weighted) |

The message: reconcile continuously to remove discovery-lag ghosts, set the retirement threshold to
the organization's security-to-cost balance, and invest in matching precision, the only lever that
lowers the floor of duplicate records from failed matches.

## Layout

```
design/PAPER19_PROTOCOL.md     Pre-registration (locked before any evaluation seed)
src/cmdb/model.py              Churn, discovery, retirement, matching; ghost/phantom error
src/run_evaluation.py          25 seeds, regime + retirement + precision sweeps
src/analyze.py                 Pre-registered hypothesis verdicts
src/make_figures.py            Figures 1 to 2
results/primary_v1/            Frozen result tables, run manifest, hypothesis summary
submission/ieee/               IEEE LaTeX source, references, figures
manuscript/paper19_draft_v0.1.md   Full manuscript
```

## Reproduce

```bash
pip install -r requirements.txt
cd src
python3 run_evaluation.py
python3 analyze.py
python3 make_figures.py
```

All randomness is seeded; `results/primary_v1/run_manifest.json` records the seeds, the lifetime,
observability mixture, cadences, and the threshold and precision sweeps.

## Data and integrity

No employer, operational, or inventory data is used. The fleet dynamics, observability, and matching
precision are synthetic with documented parameters. Model constants are fixed and not tuned on any
seed. Hypotheses, thresholds, and seeds were locked before any evaluation-seed result was inspected.
Ghost and phantom costs are reported separately, with the cost-weighted view offered as a
parameterized lens rather than a single score.
