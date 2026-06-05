# Paper 9 — Self-Trajectory Evaluation

Is HygienePrio's capacity-driven collapse intrinsic or
selection-policy-induced? Pre-registered answer: **selection-induced.**

**Target venue:** IEEE TNSM

## Headline findings (honest, pre-registered)

At K=200, W=6 mean P@50 for **HygienePrio-full** as scorer:
- HP-driven (Paper 6 baseline): **0.075** (collapse)
- HRS-driven: **0.713**
- CVSS-driven: **0.701**
- Random-driven: **0.706**
- EPSS-driven: 0.008

**The "collapse" is a closed-loop artefact of HP scoring AND
driving simultaneously.** Under any HRS-blind driver, HP holds
~0.70 at K=200.

Additional findings:
- **EPSS-self-driven at K=200 is the deepest sink** — every scorer's
  W6 P@50 collapses to ~0 (positive set itself is exhausted).
- **HP per-pair dominance over EPSS**: 1.000 under HRS/CVSS/Random
  drivers at K=200; 0.800 under HP-self; 0.393 under EPSS-self.
- **All three pre-registered hypotheses rejected** in interestingly
  different ways.

## Reproduce

From `paper9/`:
```bash
PYTHONPATH=src python3 src/run_self_traj.py    # 7,500-row sweep
PYTHONPATH=src python3 src/analyze.py          # H1-H3 + tables
PYTHONPATH=src python3 src/make_figures.py     # 2 figures
```

## Layout

```
paper9/
├── design/PAPER9_PROTOCOL.md         # pre-registration (locked 2026-06-05)
├── src/
│   ├── paper9/self_traj.py           # 5-driver x 5-scorer evaluator
│   ├── run_self_traj.py
│   ├── analyze.py
│   └── make_figures.py
├── results/primary_v1/
│   ├── self_traj_results.csv         # 7,500 rows, frozen
│   ├── cell_means.csv
│   ├── hypothesis_summary.json
│   └── run_manifest.json
└── submission/ieee/                  # 8 pages, clean compile
    ├── main.tex / main.pdf
    ├── references.bib
    ├── sections/ (12 files)
    ├── tables/ (3 files)
    └── figures/ (2 PDFs)
```

## Scientific significance

Retroactively reframes Papers 5-8's headline numbers. HygienePrio's
absolute floor at high capacity is intact whenever the deploying
organisation does not also use HygienePrio for selection — i.e., the
collapse is operationally controllable by decoupling scoring from
queue-driving.
