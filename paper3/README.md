# HygieneBench

**A reproducible synthetic benchmark for cyber-hygiene anomaly detection across identity, endpoint, and patch telemetry.**

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Reproducibility](https://img.shields.io/badge/reproducibility-frozen%20seeds-brightgreen.svg)](#reproducibility)
[![Status](https://img.shields.io/badge/status-submission--ready-orange.svg)](#paper)

HygieneBench is the first open synthetic benchmark covering identity
(Active Directory) state, endpoint patch posture, and telemetry freshness
jointly under a controlled anomaly-injection model. It defines **7
anomaly-detection tasks** (T1–T7) and **12 anomaly classes** (AH-01
through AH-12), evaluated by an 8-method panel combining rule baselines
with unsupervised ML.

## Why HygieneBench

Most ML-for-security benchmarks evaluate one telemetry source at a
time. Real cyber-hygiene anomalies cross sources — a stale privileged
account (identity), a host with patch debt (endpoint), and missing
telemetry checkins (freshness) often co-occur in a single incident.
HygieneBench is the first open dataset that models these jointly with
controlled labels so detection methods can be compared on a level
field.

## Headline empirical finding (honest)

**Rule baselines beat ML on 86.2% of (condition × task × method)
configurations.** ML adds value on two specific tasks:
- **T2 (group-membership drift):** M7 temporal z-score AP = 0.951
  vs. rule baseline 0.766 (Δ = +0.185 in the C-BASE condition).
- **T5 (patch / vulnerability hygiene):** M5 OCSVM AP = 0.668 vs.
  rule baseline 0.458 (Δ = +0.210).

The 86.2% null-result is itself a contribution — most hygiene anomaly
detection literature claims ML wins without comparing against
task-specific rule baselines.

## Install

```bash
pip install hygienebench           # from PyPI (after first deposit)
pip install -e .                   # editable from this repo
```

## Quick start

### Generate a synthetic fleet

```python
from hygienebench import SyntheticHygieneGenerator, GeneratorConfig

cfg = SyntheticHygieneGenerator(GeneratorConfig(seed=42))
fleet = cfg.generate()
print(fleet.users.head())
print(f"{len(fleet.anomaly_labels)} anomaly labels injected")
```

### Run the full evaluation panel

```bash
hygienebench-generate --seeds 42,137,2024 --condition C-BASE --output ./data/
hygienebench-evaluate --data ./data/ --methods all --output ./results/
```

This reproduces the 810-run evaluation from the paper.

### Add a new detection method

Implement a detector class with `fit(X_train)` and `score(X_test)` methods
matching the existing M1–M8 interface in `src/hygienebench/evaluation/methods/`,
then add it to the evaluation registry. See `src/hygienebench/evaluation/methods/`
for canonical examples (M1 rule baseline, M5 OCSVM, M7 temporal z-score).

## What's in the box

```
src/hygienebench/
├── generator/           # EEHDA synthetic fleet generator
├── injector/            # Controlled anomaly injection (12 classes)
├── splitter/            # Train/test/calibration splits
├── evaluation/          # 8 detection methods + metrics
│   ├── methods/         #   M1 (rule), M2 (hybrid), M3-M8 (ML)
│   └── runner/          #   evaluation harness + frozen-seed support
├── cards/               # Dataset cards + provenance
├── validate/            # Schema + consistency checks
└── cli/                 # Command-line interface
```

## Tasks and methods

### Seven tasks

| ID | Task | Anomaly classes covered |
|---|---|---|
| T1 | Stale privileged accounts | AH-01, AH-02 |
| T2 | Group membership drift | AH-03, AH-04 |
| T3 | Endpoint coverage gaps | AH-06, AH-07 |
| T4 | Identity-endpoint linkage anomalies | AH-05 |
| T5 | Patch / vulnerability hygiene | AH-08, AH-09 |
| T6 | Dormant account reactivation | AH-02 |
| T7 | Telemetry missingness | AH-10, AH-11, AH-12 |

### Eight methods

| ID | Method | Type |
|---|---|---|
| M1 | Rule baseline | Task-specific rules, no training |
| M2 | Hybrid scorer | Weighted feature combination |
| M3 | Isolation Forest | Tree-based ensemble |
| M4 | LOF | Local Outlier Factor |
| M5 | OCSVM | One-Class SVM |
| M6 | Linear AE | PCA-based reconstruction |
| M7 | Temporal z-score | Statistical |
| M8 | Graph IF | Graph isolation forest (T1–T3 only) |

## Frozen evaluation results

The paper's 810-run evaluation is shipped frozen in
`results/primary_full_v1/primary_results.csv`. Reproduce with:

```bash
python -m hygienebench.evaluation.runner \
  --datasets ./datasets/ \
  --methods all \
  --output ./results/
```

Determinism: deterministic from seed list (no random state). The
generator, injector, and evaluation harness use only seeded RNGs.

## Reproducibility

- **Frozen datasets:** 15 condition × seed combinations in `datasets/`,
  bit-identical reproduction with `--seed`
- **Frozen results:** `results/primary_full_v1/primary_results.csv` (810 rows)
- **Per-task dataset cards:** `cards/` documents the schema, anomaly
  injection model, and label provenance for each task
- **Pre-registered decision protocol:** `decision_logs/` documents
  every protocol decision before evaluation, including the
  pre-registered failure rule that produced the 86.2% null result

## Paper

The accompanying paper is *"A Reproducible Synthetic Benchmark for
Cyber-Hygiene Anomaly Detection Across Identity, Endpoint, and Patch
Telemetry"* — target venue ACM CCS AISec Workshop. The submission
manuscript is in `submission/acm/`.

Cite:

```bibtex
@misc{hygienebench2026,
  author = {Malla, Harshavardhan},
  title  = {{HygieneBench}: A Reproducible Synthetic Benchmark for Cyber-Hygiene Anomaly Detection Across Identity, Endpoint, and Patch Telemetry},
  year   = {2026},
  url    = {https://github.com/Harshavardhanmalla-Labs/research-papers/tree/main/paper3},
  note   = {Manuscript on file; Zenodo DOI at camera-ready}
}
```

## Contributing

PRs welcome — particularly:
- New detection methods following the `BaseDetector` interface
- New anomaly classes following the `AnomalyInjector` interface
- New tasks (with a pre-registered protocol document in
  `decision_logs/`)
- Sensitivity-sweep results on the existing tasks

For new detection methods, please include a comparison against M1
(rule baseline) — the paper's 86.2% null finding means rule baselines
remain the relevant comparator.

## License

MIT (see `LICENSE`).

## Author

Harshavardhan Malla — Independent Researcher.
