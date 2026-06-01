# HygieneBench v0.1

**A Reproducible Synthetic Benchmark for Cyber-Hygiene Anomaly Detection
Across Identity, Endpoint, and Patch Telemetry**

[![License: MIT](https://img.shields.io/badge/Code-MIT-blue.svg)](LICENSE-CODE)
[![License: CC BY 4.0](https://img.shields.io/badge/Data-CC%20BY%204.0-lightgrey.svg)](LICENSE-DATA)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)

Accompanying paper: *HygieneBench: A Reproducible Synthetic Benchmark for Cyber-Hygiene
Anomaly Detection Across Identity, Endpoint, and Patch Telemetry* — submitted to the
ACM Workshop on Artificial Intelligence and Security (AISec), 2026.

---

## Abstract

Cyber-hygiene anomaly detection — identifying stale privileged accounts, dormant account
reactivations, endpoint coverage gaps, patch noncompliance clusters, and telemetry
missingness — is operationally important but poorly served by existing public benchmarks,
which focus predominantly on network intrusion or attack-emulation telemetry. We introduce
**HygieneBench**, an open, reproducible benchmark that jointly covers Active Directory
identity state, endpoint patch posture, vulnerability exposure, and telemetry freshness
across seven evaluation tasks (T1–T7) and twelve anomaly classes. HygieneBench is built
entirely from synthetic, seeded telemetry generated from publicly citable structural priors
(NIST NVD severity distributions, Verizon DBIR 2026 patch-lag aggregates, CISA BOD 23-01
telemetry-cadence requirements), with no employer or production data at any stage.

We evaluate eight methods across five telemetry conditions. Applying a pre-registered
failure protocol, we find that **86.2% of (condition, task, method) configurations fail to
outperform the rule baseline**, with ML adding meaningful signal on T2 (group-membership-drift
detection, best ML: +0.185 AP over rule) and T5 (patch-vulnerability hygiene, best ML:
+0.210 AP over rule). We release the generator, datasets, and evaluation harness to enable
reproducible comparison of future methods.

---

## Key Results

| Finding | Value |
|---|---|
| Total evaluation runs | 810 (7 tasks x 8 methods x 5 conditions x 3 seeds) |
| ML failure rate (pre-registered threshold: delta >= 0.05 AP in >= 2/3 seeds) | **86.2%** of configurations |
| Best ML gain — T2 group-membership drift (M7 temporal z-score) | **+0.185 AP** over rule baseline |
| Best ML gain — T5 patch-vulnerability hygiene (M5 OCSVM) | **+0.210 AP** over rule baseline |
| Rule baseline mean AP across all configs | 0.916 |
| Telemetry staleness effect (C-STALE worst case, T3) | -0.168 AP degradation |

ML adds consistent, meaningful value on only two of seven tasks. Simple rule baselines
dominate tasks with strong single-feature discriminators (T1, T4, T6, T7). The
graph-augmented method (M8) is failure-flagged on 100% of configurations.

---

## Repository Structure

```
paper3/
├── src/
│   ├── hygienebench/              # Core Python package
│   │   ├── generator.py           # Seeded synthetic data generator
│   │   ├── injector.py            # Anomaly injection (AH-01 through AH-12)
│   │   ├── schema.py              # Table schemas (11 entity/event tables)
│   │   ├── config.py              # Condition and seed configuration
│   │   ├── splitter.py            # Stratified train/val/test split logic
│   │   ├── validate.py            # Dataset integrity checks
│   │   ├── cards.py               # Dataset card generation
│   │   ├── cli.py                 # Command-line interface
│   │   └── evaluation/
│   │       ├── features.py        # Task-scoped feature extraction (T1-T7)
│   │       ├── methods.py         # 8 detection methods (M1-M8)
│   │       ├── metrics.py         # AP, P@k, BCa bootstrap CI
│   │       └── runner.py          # Full evaluation loop
│   └── run_evaluation.py          # Entry point for re-running the full evaluation
├── datasets/                      # 15 frozen dataset instances (5 conditions x 3 seeds)
│   ├── hygienebench_v0.1_c_base_seed42_n1000/
│   ├── hygienebench_v0.1_c_base_seed137_n1000/
│   ├── hygienebench_v0.1_c_base_seed2024_n1000/
│   ├── hygienebench_v0.1_c_stale_seed42_n1000/
│   ├── hygienebench_v0.1_c_stale_seed137_n1000/
│   ├── hygienebench_v0.1_c_stale_seed2024_n1000/
│   ├── hygienebench_v0.1_c_fresh_seed42_n1000/
│   ├── hygienebench_v0.1_c_fresh_seed137_n1000/
│   ├── hygienebench_v0.1_c_fresh_seed2024_n1000/
│   ├── hygienebench_v0.1_c_miss_seed42_n1000/
│   ├── hygienebench_v0.1_c_miss_seed137_n1000/
│   ├── hygienebench_v0.1_c_miss_seed2024_n1000/
│   ├── hygienebench_v0.1_c_unsup_seed42_n1000/
│   ├── hygienebench_v0.1_c_unsup_seed137_n1000/
│   └── hygienebench_v0.1_c_unsup_seed2024_n1000/
├── results/
│   └── primary_full_v1/           # Frozen evaluation results (810 runs)
│       ├── primary_results.csv    # AP, P@k per (condition, task, method, seed)
│       ├── failure_flags.csv      # Failure flag per (condition, task, method)
│       ├── rank_stability.csv     # AP rank stability CV across seeds
│       └── run_manifest.json      # Dataset paths, seeds, software versions
├── design/
│   ├── SCHEMA_v0_1.md             # Full 11-table schema specification
│   ├── EXPERIMENTAL_DESIGN_v0_1.md
│   └── TASK_SPECS.md              # 7-task specification with k values and imbalance ratios
├── manuscript/
│   └── figures/                   # Publication-quality figures (vector PDF)
│       ├── fig1_ap_heatmap.pdf
│       ├── fig2_failure_heatmap.pdf
│       ├── fig3_ap_by_condition.pdf
│       └── fig4_t2_t5_ml_gain.pdf
├── submission/
│   └── acm/                       # ACM LaTeX scaffold (main.tex, sections/, tables/)
├── pyproject.toml
└── README.md                      # This file
```

---

## Requirements

- **Python:** 3.9 or later
- **Core packages:** `numpy >= 1.24`, `pandas >= 2.0`, `scipy >= 1.10`
- **Evaluation packages:** `scikit-learn >= 1.2`, `networkx >= 3.0`

All dependencies are declared in `pyproject.toml`. No GPU or PyTorch required —
all methods run on CPU with standard scientific Python libraries.

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/[author]/hygienebench.git
cd hygienebench

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# Install the package and dependencies
pip install -e .
```

### Option A — Reproduce results from the frozen datasets

The 15 dataset instances in `datasets/` are the exact instances used in the paper.
To reproduce the full 810-run evaluation:

```bash
python src/run_evaluation.py \
    --datasets-dir datasets/ \
    --output-dir results/my_replication/ \
    --seeds 42 137 2024 \
    --conditions c_base c_fresh c_stale c_miss c_unsup
```

Expected output: `primary_results.csv` with 810 rows.
Compare against `results/primary_full_v1/primary_results.csv` for exact reproducibility.

### Option B — Generate fresh datasets from scratch

```bash
# Generate a single dataset instance (fully reproducible from seed)
python -m hygienebench generate \
    --condition c_base \
    --seed 42 \
    --n-entities 1000 \
    --output datasets/my_generated/

# Validate the generated dataset
python -m hygienebench validate datasets/my_generated/
```

Available conditions: `c_base`, `c_fresh`, `c_stale`, `c_miss`, `c_unsup`

Each dataset folder contains 12 CSV tables and a `dataset_card.json`:

```
hygienebench_v0.1_c_base_seed42_n1000/
├── users.csv
├── groups.csv
├── computers.csv
├── assets.csv
├── login_events.csv
├── group_membership_events.csv
├── account_lifecycle_events.csv
├── endpoint_patch_state.csv
├── vulnerability_records.csv
├── remediation_events.csv
├── telemetry_freshness_log.csv
├── anomaly_labels.csv          # ground-truth labels with benchmark_task_id and split
└── dataset_card.json           # generation metadata and structural prior citations
```

---

## Dataset Description

HygieneBench v0.1 covers **7 evaluation tasks**, **12 anomaly classes**, and
**5 telemetry conditions**, producing 810 (condition, task, method, seed) evaluation
configurations across 15 dataset instances (5 conditions x 3 seeds).

### Dataset Scale (per instance, n=1,000 users)

| Table | Approx. rows | Description |
|---|---|---|
| `users` | 1,000 | AD user accounts with identity state attributes |
| `groups` | 65 | AD security and distribution groups |
| `computers` | 830 | Managed endpoints |
| `assets` | 830 | Asset inventory entries |
| `login_events` | ~249,000 | Authentication events (30-day window) |
| `group_membership_events` | ~51 | Group add/remove events (30-day window) |
| `endpoint_patch_state` | 830 | Per-endpoint patch compliance snapshot |
| `vulnerability_records` | ~3,500 | Per-endpoint CVE exposure records |
| `anomaly_labels` | 110 | Ground-truth labels with task ID and split |

### Telemetry Conditions (5)

| ID | Description |
|---|---|
| C-BASE | No artificial staleness; all sources current |
| C-FRESH | Elevated freshness flagging; sources verified current |
| C-STALE | 20% of entities have heavy-stale telemetry (>14 days gap) |
| C-MISS | One data source absent for 15% of entities |
| C-UNSUP | C-BASE with anomaly labels withheld from the training pipeline |

### Anomaly Classes (12)

| Code | Class | Primary Tasks |
|---|---|---|
| AH-01 | Stale privileged account | T1 |
| AH-02 | Privilege escalation drift | T7 |
| AH-03 | Group membership drift | T2 |
| AH-04 | Dormant account reactivation | T6 |
| AH-05 | Impossible or unusual login | T1, T3 |
| AH-06 | Endpoint-identity risk correlation | T3 |
| AH-07 | Patch noncompliance cluster | T5 |
| AH-08 | KEV exposure aging | T5 |
| AH-09 | Asset inventory mismatch | T4 |
| AH-10 | Missing endpoint agent | T4 |
| AH-11 | Telemetry missingness cluster | T4 |
| AH-12 | Abnormal remediation delay | T5 |

### Benchmark Tasks (7)

| Task | Description | Entity scope | k | Imbalance |
|---|---|---|---|---|
| T1 | Stale privileged account risk | Privileged users | 10 | 1:50 |
| T2 | Group membership drift | Users with group events | 20 | 1:167 |
| T3 | Endpoint-identity risk correlation | Users with endpoints | 15 | 1:333 |
| T4 | Telemetry coverage gaps | All computers/assets | 20 | 1:14 |
| T5 | Patch-vulnerability hygiene | All computers | 25 | 1:59 |
| T6 | Dormant account reactivation | Users with lifecycle events | 10 | 1:250 |
| T7 | Escalation drift detection | Users with group add events | 10 | 1:500 |

### Structural Priors (publicly citable)

All generator parameters are derived from public sources — no proprietary or
operational data was used:

- **Verizon DBIR 2026:** 43-day median critical patch lag (T5 anomaly thresholds)
- **NIST NVD:** CVE severity distributions (vulnerability record generation)
- **CISA BOD 23-01:** 14-day asset discovery and 72-hour telemetry cadence requirements

### Evaluation Summary (810 runs: 7 tasks x 8 methods x 5 conditions x 3 seeds)

| Method | Mean AP | Failure rate |
|---|---|---|
| M1 — Rule baseline | 0.916 | — (reference) |
| M5 — OCSVM | 0.913 | 69.5% |
| M4 — LOF | 0.800 | 77.1% |
| M6 — Linear-AE | 0.798 | 88.6% |
| M3 — Isolation Forest | 0.796 | 84.8% |
| M7 — Temporal z-score | 0.793 | 84.8% |
| M2 — Hybrid scorer | 0.709 | 95.2% |
| M8 — Graph-IF | 0.801 | 100% |

Failure rate = fraction of (condition, task) pairs where the method does not improve
on M1 by >= 0.05 AP in >= 2/3 seeds (pre-registered protocol).

---

## Frozen Results

`results/primary_full_v1/` contains the exact output used in the paper:

| File | Rows | Description |
|---|---|---|
| `primary_results.csv` | 810 | AP, P@k per (condition, task, method, seed) |
| `failure_flags.csv` | 705 | Failure flag per (condition, task, method) — 3-seed majority vote |
| `rank_stability.csv` | 105 | AP rank stability CV across seeds |
| `run_manifest.json` | — | Dataset paths, seeds, condition IDs, software versions |

---

## Citation

If you use HygieneBench in your research, please cite:

```bibtex
@inproceedings{malla2026hygienebench,
  title     = {{HygieneBench}: A Reproducible Synthetic Benchmark for
               Cyber-Hygiene Anomaly Detection Across Identity,
               Endpoint, and Patch Telemetry},
  author    = {Malla, Harshavardhan},
  booktitle = {Proceedings of the ACM Workshop on Artificial Intelligence
               and Security (AISec)},
  year      = {2026},
  doi       = {10.5281/zenodo.20438401},
  url       = {https://doi.org/10.5281/zenodo.20438401}
}
```

---

## Zenodo Artifact

A full dataset and artifact archive is available on Zenodo. DOI: [to be finalized at
camera-ready submission]

The Zenodo archive includes the complete frozen datasets, evaluation harness, and
publication figures. Code repository: `https://github.com/[author]/hygienebench`

---

## License

- **Code** (`src/`): [MIT License](LICENSE-CODE)
- **Datasets** (`datasets/`), **Results** (`results/`), **Design docs** (`design/`):
  [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE-DATA)

---

## Data Statement

All data in this repository are **fully synthetic and seeded**. No real usernames,
hostnames, IP addresses, employee records, patch data, or operational telemetry
from any organization were used at any stage of data generation. The synthetic
generator uses only publicly citable structural priors (NIST NVD, Verizon DBIR 2026,
CISA BOD 23-01). Entity identifiers are deterministic UUIDs derived from seeded hashes.
