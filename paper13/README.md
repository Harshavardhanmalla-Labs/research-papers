# Policy-as-Code for CJIS Compliance: Prevention versus Detection

Code and frozen results for the paper. When is preventive policy-as-code (block a violating change
at the door) worth more than detective auto-remediation (detect and fix after the fact) for CJIS
control violations on law-enforcement endpoint fleets? A pre-registered simulation of a
500-endpoint fleet over one year, sweeping the violation recurrence rate.

## Headline result (25 pre-registered seeds, 900 to 924)

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1: prevention cuts CJI exposure by at least 50% at typical recurrence | SUPPORTED | 70.3% reduction, interval [70.0, 70.6] |
| H2: the reduction is capped by the blockable share | SUPPORTED | reduction 0.703 vs blockable share 0.753 (5% slip through) |
| H3: the advantage grows with violation recurrence | SUPPORTED | 0% to 31% to 57% to 70% to 81% across the recurrence sweep |
| H4: the false-block cost is recurrence-independent | SUPPORTED | 0.30 false blocks per endpoint-month, under 1% variation across the sweep |

The message: prevention's security benefit grows with how often misconfigurations recur, while its
operational cost (benign changes wrongly blocked) stays fixed, so the benefit-to-cost ratio rises
with recurrence. High-churn fleets most favor prevention; emergent violations (certificate expiry)
form a floor that no guardrail can block.

## Layout

```
design/PAPER13_PROTOCOL.md     Pre-registration (locked before any evaluation seed)
src/policyascode/model.py      Violation processes, detective and preventive regimes, false blocks
src/run_evaluation.py          25 seeds x 5 recurrence levels
src/analyze.py                 Pre-registered hypothesis verdicts
src/make_figures.py            Figures 1 to 2
results/primary_v1/            Frozen result tables, run manifest, hypothesis summary
submission/ieee/               IEEE LaTeX source, references, figures
manuscript/paper13_draft_v0.1.md   Full manuscript
```

## Reproduce

```bash
pip install -r requirements.txt
cd src
python3 run_evaluation.py
python3 analyze.py
python3 make_figures.py
```

All randomness is seeded; `results/primary_v1/run_manifest.json` records the seeds, event rates,
the recurrence sweep, and the false-positive rate.

## Data and integrity

No employer, operational, or CJIS audit data is used. The fleet and its event rates are synthetic
with documented priors. Model constants are fixed and not tuned on any seed. Hypotheses,
thresholds, and seeds were locked before any evaluation-seed result was inspected. Security
exposure and operational false blocks are reported separately rather than netted into one score.
