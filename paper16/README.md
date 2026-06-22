# Multivariate Machine Learning for Cyber-Hygiene Anomaly Detection

Code and frozen results for the paper. Does multivariate ML anomaly detection earn its complexity
over the per-signal threshold rules security teams already run for endpoint hygiene telemetry, and
when? A pre-registered evaluation on a synthetic fleet with two anomaly types: a single-channel
spike (threshold-crossing) and a cross-channel correlation violation (individually normal, jointly
anomalous).

## Headline result (25 pre-registered seeds, 700 to 724)

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1: joint detection beats rules on cross-channel anomalies by at least 0.10 AP | SUPPORTED | Mahalanobis 0.710 vs Rule-Max 0.103, difference +0.607, interval [0.598, 0.617] |
| H2: rules win on single-channel anomalies | SUPPORTED | Rule-Max 0.836, best joint (Isolation Forest) 0.740 |
| H3: the gain needs joint modeling, not aggregation | SUPPORTED | structure-blind Rule-Count 0.084 vs Mahalanobis 0.710 |
| H4: on a mixture, joint wins but by a smaller margin | SUPPORTED | Mahalanobis 0.702 vs Rule-Max 0.473 (< the cross-channel-only margin) |

The choice of ML method is decisive: covariance-aware (Mahalanobis 0.71) and density-aware (Local
Outlier Factor 0.64) detectors see the correlation violation, while the popular axis-aligned
Isolation Forest (0.11) does not. The recommendation is a two-tier monitor: cheap rules for obvious
single-channel anomalies, a covariance- or density-aware detector for subtle cross-channel ones.

## Layout

```
design/PAPER16_PROTOCOL.md     Pre-registration (locked before any evaluation seed)
src/hygieneml/model.py         Telemetry generator, six detectors, average-precision evaluation
src/run_evaluation.py          25 seeds x 3 conditions x 6 detectors
src/analyze.py                 Pre-registered hypothesis verdicts
src/make_figures.py            Figures 1 to 2
results/primary_v1/            Frozen result tables, run manifest, hypothesis summary
submission/ieee/               IEEE LaTeX source, references, figures
manuscript/paper16_draft_v0.1.md   Full manuscript
```

## Reproduce

```bash
pip install -r requirements.txt
cd src
python3 run_evaluation.py   # 25 seeds x 3 conditions x 6 detectors
python3 analyze.py          # hypothesis verdicts
python3 make_figures.py     # figures
```

All randomness is seeded; `results/primary_v1/run_manifest.json` records the seeds, the
anomaly-model constants, and the detector settings.

## Data and integrity

No employer, operational, or real telemetry data is used. The fleet and its hygiene telemetry are
synthetic with documented distributions. Detector hyperparameters are fixed at library defaults and
not tuned on any seed. Hypotheses, thresholds, and seeds were locked before any evaluation-seed
result was inspected.
