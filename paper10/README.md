# Paper 10 — AutoHeal: A Pre-Registered Self-Healing Framework for Autonomous Vulnerability Remediation

A synthesis paper integrating Papers 3–9 into a six-stage closed-loop
framework with pre-registered safety bounds. Evaluated on 2,700 frozen
window-seed rows using the EEHDA fleet + real EPSS/KEV public corpus.

**Target venue:** IEEE TNSM

## Headline findings (honest, pre-registered)

| H | Statement | Outcome |
|---|-----------|---------|
| H1 | Coverage ≥ 80% at W6 (K ∈ {50, 100}) | **Supported** — 97.8% achieved (+18 pp) |
| H2 | Per-window rollback rate ≤ 5% | **Rejected** — 300 of 900 windows fail; max 100% |
| H3 | MTTR ≤ 50% of human-in-loop | **Not analysable** — instrumentation issue (honestly reported) |
| H4 | Per-window dominance ≥ 80% | **Rejected** — 2% dominance (HIL's wider capacity catches up) |

Safety hard-stop fired 134 times (14.9% of windows); cascading failures detected 3 times. **The safety mechanism works as designed.** AutoHeal achieves automation parity with human-in-loop at the pre-registered conservative triage thresholds, not throughput superiority.

## The six-stage AutoHeal pipeline

```
Detect → Score → Triage → Plan → Act → Verify+Rollback → Learn
```

- **Triage** (AUTO / REVIEW / DEFER) gated by HygienePrio score ≥ 0.80 + host non-CRITICAL + test suite present.
- **Act** with pre-registered failure-mode distribution (92% success / 5% rollback / 3% deferred).
- **Verify** with hard-stop at >10% rollback rate per window or cascading-failure detection.
- **Learn** uses Paper 7 lag-1 calibration (only at K ≤ 100; held fixed at K = 200 per Paper 9 Corollary 4).

## Pre-registration

Locked 2026-06-05 at `paper10/design/PAPER10_PROTOCOL.md`. Architecture parameters, triage thresholds, failure-mode distribution, safety bounds, and hypotheses fixed before any evaluation-seed AutoHeal result was inspected.

## Reproduce

```bash
PYTHONPATH=src python3 src/run_autoheal.py     # 2,700-row frozen sweep
PYTHONPATH=src python3 src/analyze.py          # H1-H4 outcomes + LaTeX tables
```

Dependencies: Paper 4's `hygieneprio` + Paper 5's `paper5.window_sim` + `real_data/processed/cve_corpus_for_sampling.csv`.

## Layout

```
paper10/
├── design/PAPER10_PROTOCOL.md
├── src/
│   ├── autoheal/                    # framework package
│   │   ├── framework.py             # six-stage pipeline orchestrator
│   │   ├── triage.py                # AUTO/REVIEW/DEFER classifier
│   │   ├── actuator.py              # simulated patch operation
│   │   ├── verifier.py              # health check + cascading-failure detector
│   │   └── baselines.py             # human-in-loop + fixed-policy
│   ├── run_autoheal.py
│   └── analyze.py
├── results/primary_v1/
│   ├── autoheal_results.csv         # 2,700 rows, frozen
│   ├── hypothesis_summary.json
│   └── run_manifest.json
└── submission/ieee/                 # 8 pages, clean compile
    ├── main.tex / main.pdf
    ├── references.bib
    ├── sections/ (12 files)
    └── tables/ (4 files)
```

## Honest scope

AutoHeal cannot patch real systems. The evaluation is on the EEHDA synthetic fleet with real CVE attribute distributions. The pre-registered failure-mode distribution (92/5/3) is drawn from public sysadmin literature, not measured on a real fleet. Real validation is identified as the most consequential remaining direction.
