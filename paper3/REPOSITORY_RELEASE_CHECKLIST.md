# HygieneBench v0.1 — Repository & Zenodo Release Checklist

**Version:** v0.1-submission
**Prepared:** 2026-05-28
**Status:** PENDING DEPOSIT — do not publish DOI until all items are checked.

---

## Artifact Identity

| Field | Value |
|---|---|
| GitHub repository URL | `[TO BE FILLED]` |
| Zenodo DOI | `10.5281/zenodo.20438401` |
| Zenodo URL | `https://doi.org/10.5281/zenodo.20438401` |
| Zenodo deposit date | 2026-05-29 |
| Artifact version tag | `v0.1-submission` |
| Zenodo community | zenodo.org/communities/cs-security (or cs.CR equivalent) |
| License | MIT (code) / CC BY 4.0 (datasets and documentation) |

---

## Files to INCLUDE in the artifact

### Source code (`src/`)
- [ ] `src/hygienebench/__init__.py`
- [ ] `src/hygienebench/schema.py`
- [ ] `src/hygienebench/config.py`
- [ ] `src/hygienebench/generator.py`
- [ ] `src/hygienebench/injector.py`
- [ ] `src/hygienebench/splitter.py`
- [ ] `src/hygienebench/cards.py`
- [ ] `src/hygienebench/cli.py`
- [ ] `src/hygienebench/validate.py`
- [ ] `src/hygienebench/evaluation/__init__.py`
- [ ] `src/hygienebench/evaluation/features.py`
- [ ] `src/hygienebench/evaluation/methods.py`
- [ ] `src/hygienebench/evaluation/metrics.py`
- [ ] `src/hygienebench/evaluation/runner.py`
- [ ] `src/run_evaluation.py`

### Package metadata
- [ ] `pyproject.toml`
- [ ] `README.md` (create before release — not yet drafted)

### Frozen datasets (`datasets/`)
- [ ] `datasets/hygienebench_v0.1_c_base_seed42_n1000/` (all CSVs + dataset_card.json)
- [ ] `datasets/hygienebench_v0.1_c_base_seed137_n1000/`
- [ ] `datasets/hygienebench_v0.1_c_base_seed2024_n1000/`
- [ ] `datasets/hygienebench_v0.1_c_stale_seed42_n1000/`
- [ ] `datasets/hygienebench_v0.1_c_stale_seed137_n1000/`
- [ ] `datasets/hygienebench_v0.1_c_stale_seed2024_n1000/`
- [ ] `datasets/hygienebench_v0.1_c_fresh_seed42_n1000/`
- [ ] `datasets/hygienebench_v0.1_c_fresh_seed137_n1000/`
- [ ] `datasets/hygienebench_v0.1_c_fresh_seed2024_n1000/`
- [ ] `datasets/hygienebench_v0.1_c_miss_seed42_n1000/`
- [ ] `datasets/hygienebench_v0.1_c_miss_seed137_n1000/`
- [ ] `datasets/hygienebench_v0.1_c_miss_seed2024_n1000/`
- [ ] `datasets/hygienebench_v0.1_c_unsup_seed42_n1000/`
- [ ] `datasets/hygienebench_v0.1_c_unsup_seed137_n1000/`
- [ ] `datasets/hygienebench_v0.1_c_unsup_seed2024_n1000/`

### Results (`results/primary_full_v1/`)
- [ ] `results/primary_full_v1/primary_results.csv`
- [ ] `results/primary_full_v1/failure_flags.csv`
- [ ] `results/primary_full_v1/rank_stability.csv`
- [ ] `results/primary_full_v1/run_manifest.json`

### Design documentation (`design/`)
- [ ] `design/SCHEMA_v0_1.md`
- [ ] `design/EXPERIMENTAL_DESIGN_v0_1.md`
- [ ] `design/TASK_SPECS.md`

### Figures (`manuscript/figures/`)
- [ ] `manuscript/figures/fig1_ap_heatmap.pdf`
- [ ] `manuscript/figures/fig2_failure_heatmap.pdf`
- [ ] `manuscript/figures/fig3_ap_by_condition.pdf`
- [ ] `manuscript/figures/fig4_t2_t5_ml_gain.pdf`

### Reproducibility scripts
- [ ] `tests/` directory (if any reproducibility test scripts exist)

---

## Files to EXCLUDE from the artifact

| File / Pattern | Reason |
|---|---|
| `.venv/` | Virtual environment — not portable |
| `__pycache__/` | Compiled bytecode — auto-generated |
| `*.pyc` | Compiled bytecode |
| `.env`, `*.env` | Environment variable files — may contain secrets |
| `manuscript/paper_draft_v0.1.md` | Pre-publication manuscript — do not release until accepted |
| `manuscript/supplemental_appendix_v0.1.md` | Pre-publication — same |
| `manuscript/PAPER3_DECISION_LOG.md` | Internal research log — not for public release |
| `manuscript/STEP1_RESEARCH_VALIDATION.md` | Internal research log |
| `submission/` | Venue-specific submission files — not part of artifact |
| `PAPER3_SUBMISSION_CHECKLIST.md` | Internal checklist |
| `REPOSITORY_RELEASE_CHECKLIST.md` | This file — internal |
| `FIGURE_QUALITY_CHECK.md` | Internal QA — not for artifact |
| `results/primary_full_v1/run_log.txt` | Verbose runtime log — optional; review before including |
| `decision_logs/` | Internal — if present |
| `feasibility/` | Internal prior-art research notes — not for public release |
| `references/` | Internal reference management — not for artifact |
| Any file containing real user, host, or IP data | Constraint: all data must be synthetic and seeded |

---

## Pre-release verification steps

### Code
- [ ] All Python files have no hardcoded personal paths or credentials
- [ ] Generator runs end-to-end from scratch: `python -m hygienebench generate --condition c_base --seed 42 --output /tmp/test_gen`
- [ ] Validation passes on generated dataset: `python -m hygienebench validate /tmp/test_gen`
- [ ] Evaluation runner produces results matching `primary_results.csv` when re-run from frozen datasets

### Data
- [ ] All 15 datasets contain only synthetic, seeded data — no real usernames, hostnames, IPs
- [ ] All `dataset_card.json` files present and contain correct generation metadata
- [ ] `anomaly_labels.csv` present in each dataset with `benchmark_task_id` and `split` columns

### Results
- [ ] `run_manifest.json` correctly references condition IDs and seed values
- [ ] `primary_results.csv` has exactly 810 rows
- [ ] `failure_flags.csv` has exactly 705 rows

### Documentation
- [ ] `README.md` created and covers: installation, quick-start, dataset structure, evaluation re-run command
- [ ] License files present for both code (MIT) and data (CC BY 4.0)
- [ ] Zenodo deposit metadata: title, description, authors, keywords (`cyber-hygiene`, `anomaly-detection`, `benchmark`, `synthetic-data`), related publication DOI (add after paper DOI assigned)

---

## Post-deposit steps

1. Copy the Zenodo DOI into `paper_draft_v0.1.md` §7 Conclusion placeholder `[repository URL to be added]`.
2. Copy the GitHub URL into §7 Conclusion (same placeholder — use format: `https://zenodo.org/record/XXXXXXX`).
3. Rebuild LaTeX PDF with updated §7.
4. Confirm the Zenodo record is public before submitting paper.

---

*Internal document — do not include in artifact release.*
