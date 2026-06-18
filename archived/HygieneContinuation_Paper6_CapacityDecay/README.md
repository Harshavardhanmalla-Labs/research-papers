# Paper 6 — Capacity-Indexed Decay of Exploit-Likelihood Vulnerability Prioritization

A pre-registered two-dimensional sweep over remediation capacity $K$ and
CVE arrival rate $\lambda$ extending Paper 5's multi-window simulation.

**Target venue:** IEEE Transactions on Network and Service Management (TNSM)

## Headline findings (honest, pre-registered)

- **EPSS-only decays in all 20 cells** (slope range $-0.013$ to $-0.064$ P@50/window).
- **Predicted monotone scaling rejected** — Spearman correlations across most slices fall well below the $|\rho| \geq 0.8$ pre-registered threshold.
- **HygienePrio-full also collapses at high capacity** — H4 rejected. At $K = 200, \lambda = 1$ the W6 mean falls to **0.062**.
- **Per-pair dominance survives** — HygienePrio beats EPSS in **2,881/3,000 (96.0%)** of (cell, seed, window) comparisons; minimum per-cell dominance 76.7%.

## Reproduce

From `paper6/`:
```bash
PYTHONPATH=src python3 src/run_sweep.py        # 15,000-row frozen sweep
PYTHONPATH=src python3 src/analyze_sweep.py    # H1–H4 outcomes + LaTeX tables
PYTHONPATH=src python3 src/make_figures.py     # 3 figures
```

## Repository layout

```
paper6/
├── design/PAPER6_PROTOCOL.md       # pre-registration (locked 2026-06-04)
├── src/
│   ├── paper6/sweep_eval.py        # (K, λ) sweep driver
│   ├── run_sweep.py                # CLI entry
│   ├── analyze_sweep.py            # H1–H4 + table generation
│   └── make_figures.py             # 3 figures
├── results/primary_sweep_v1/
│   ├── sweep_results.csv           # 15,000 rows, frozen
│   ├── cell_summary.csv            # per-cell aggregates with bootstrap CIs
│   ├── persistence.csv             # per-cell HP vs EPSS dominance fraction
│   ├── hypothesis_summary.json     # H1–H4 outcomes
│   └── run_manifest.json
└── submission/ieee/                # IEEE TNSM scaffold, compiles 8 pages
    ├── main.tex
    ├── main.pdf
    ├── references.bib
    ├── sections/ (12 files)
    ├── tables/ (4 files)
    └── figures/ (3 PDFs)
```

## Dependencies

Re-uses Paper 4's `hygieneprio` package and Paper 5's `paper5.window_sim`
via `sys.path` injection in `paper6.sweep_eval`. No code duplication.
