#!/usr/bin/env python3
"""Evaluation-metrics smoke on a tiny deterministic toy.

No experiment run, no fake paper results. Demonstrates the metric APIs
on 5 pairs across three strategies (random, epss_only, oracle).
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from paper1.evaluation.compliance_metrics import (
    capacity_efficiency,
    kev_deadline_breach_rate,
)
from paper1.evaluation.eehda import compute_ehd, eehda_report
from paper1.evaluation.ranking_metrics import ndcg_at_k, precision_at_k, recall_at_k

END = date(2025, 12, 31)
PAIRS = ["p1", "p2", "p3", "p4", "p5"]


def main() -> int:
    ranking = pd.DataFrame(
        {"pair_id": PAIRS, "rank": [1, 2, 3, 4, 5], "priority_score": [0.9, 0.8, 0.7, 0.6, 0.5]}
    )
    labels = pd.DataFrame(
        {
            "pair_id": PAIRS,
            "label": [True, False, True, False, True],
            "label_date": [date(2025, 6, 10)] * 5,
        }
    )

    # Three toy schedule histories with different remediation timing.
    sched = {
        "oracle": pd.DataFrame({  # remediates the positives promptly
            "pair_id": ["p1", "p3", "p5"],
            "effective_remediation_time": [date(2025, 6, 11)] * 3,
        }),
        "epss_only": pd.DataFrame({
            "pair_id": ["p1", "p3"],
            "effective_remediation_time": [date(2025, 6, 20), date(2025, 6, 25)],
        }),
        "random": pd.DataFrame({
            "pair_id": ["p2"],
            "effective_remediation_time": [date(2025, 6, 30)],
        }),
    }
    ehd = {name: compute_ehd(df, labels, END) for name, df in sched.items()}

    kev = pd.DataFrame({"pair_id": ["p1", "p3"], "kev_due_date": [date(2025, 6, 15), date(2025, 6, 15)]})

    print("=== ranking metrics (top-3) ===")
    print(f"  precision@3: {precision_at_k(ranking, labels, 3):.4f}")
    print(f"  recall@3:    {recall_at_k(ranking, labels, 3):.4f}")
    print(f"  nDCG@3:      {ndcg_at_k(ranking, labels, 3):.4f}")

    print("=== EHD by strategy (simulated days) ===")
    for name in sorted(ehd):
        print(f"  {name:14s}: {ehd[name]:.1f}")

    print("=== EEHDA report ===")
    report = eehda_report(ehd)
    for _, r in report.iterrows():
        print(f"  {r['strategy']:14s} abs={r['absolute']:.1f} "
              f"rel_random={r['relative_to_random']} frac_oracle={r['fraction_of_oracle']}")

    print("=== compliance ===")
    print(f"  KEV breach (epss_only sched): {kev_deadline_breach_rate(sched['epss_only'], kev)}")
    print(f"  capacity efficiency (epss):   "
          f"{capacity_efficiency(sched['epss_only'][['pair_id']], labels):.4f}")
    print("NOTE: statistical tests and real experiment aggregation arrive later.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
