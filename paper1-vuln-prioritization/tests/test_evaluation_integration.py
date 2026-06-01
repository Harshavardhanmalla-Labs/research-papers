"""Evaluation metrics integration smoke (all layers together, toy data)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from paper1.audit.hash_chain import AuditLogger
from paper1.evaluation.audit_metrics import (
    audit_explanation_completeness,
    hash_chain_validity,
)
from paper1.evaluation.compliance_metrics import (
    capacity_efficiency,
    kev_deadline_breach_rate,
)
from paper1.evaluation.eehda import compute_ehd, eehda_report
from paper1.evaluation.metrics import aggregate_metrics
from paper1.evaluation.ranking_metrics import ndcg_at_k, precision_at_k, recall_at_k
from paper1.evaluation.scheduler_metrics import scheduler_feasibility_rate
from paper1.model.weights import FEATURE_COLUMNS

END = date(2025, 12, 31)


def test_full_metrics_pipeline(tmp_path: Path):
    pairs = ["p1", "p2", "p3", "p4", "p5"]
    ranking = pd.DataFrame({"pair_id": pairs, "rank": [1, 2, 3, 4, 5],
                            "priority_score": [0.9, 0.8, 0.7, 0.6, 0.5]})
    labels = pd.DataFrame({
        "pair_id": pairs,
        "label": [True, False, True, False, True],
        "label_date": [date(2025, 6, 10), date(2025, 6, 10), date(2025, 6, 10),
                       date(2025, 6, 10), date(2025, 6, 10)],
    })

    # ranking metrics
    p3 = precision_at_k(ranking, labels, 3)
    r3 = recall_at_k(ranking, labels, 3)
    n3 = ndcg_at_k(ranking, labels, 3)
    assert 0.0 <= p3 <= 1.0
    assert 0.0 <= r3 <= 1.0
    assert 0.0 <= n3 <= 1.0

    # EHD by strategy
    sched_proposed = pd.DataFrame({
        "pair_id": ["p1", "p3"],
        "strategy_name": ["proposed_full", "proposed_full"],
        "effective_remediation_time": [date(2025, 6, 12), date(2025, 6, 11)],
    })
    sched_random = pd.DataFrame({
        "pair_id": ["p2"],
        "strategy_name": ["random"],
        "effective_remediation_time": [date(2025, 6, 30)],
    })
    ehd = {
        "random": compute_ehd(sched_random, labels, END),
        "proposed_full": compute_ehd(sched_proposed, labels, END),
        "oracle": 0.0,
        "epss_only": compute_ehd(sched_proposed, labels, END),
    }
    report = eehda_report(ehd)
    assert {"absolute", "relative_to_random", "relative_to_epss", "fraction_of_oracle"} <= set(report.columns)
    assert not report.empty

    # KEV breach
    kev = pd.DataFrame({"pair_id": ["p1", "p3"], "kev_due_date": [date(2025, 6, 11), date(2025, 6, 11)]})
    breach = kev_deadline_breach_rate(sched_proposed, kev)
    # p1 remediated 6-12 (late), p3 6-11 (on time) -> 0.5
    assert breach == 0.5

    # capacity efficiency
    scheduled_pairs = pd.DataFrame({"pair_id": ["p1", "p3"]})
    ce = capacity_efficiency(scheduled_pairs, labels)
    assert ce == 1.0  # both p1, p3 are positive

    # audit metrics from a temp log of two score records
    logger = AuditLogger(tmp_path / "audit.jsonl")
    for i in range(2):
        logger.append(
            record_id=f"ADR-{i}", pair_id=f"H:{i}", window_id="W-1", decision_type="score",
            priority_score=0.5,
            feature_values=dict.fromkeys(FEATURE_COLUMNS, 0.5),
            feature_contributions=dict.fromkeys(FEATURE_COLUMNS, 0.1),
            weights_version="w_logit-v1", data_feed_versions={"nvd": "2026-05-26"},
            framework_version="paper1-0.1.0",
            created_at=datetime(2026, 5, 26, 12, 0, tzinfo=UTC),
        )
    assert audit_explanation_completeness(logger.path) == 1.0
    assert hash_chain_validity(logger.path) is True

    # scheduler metrics from fake ScheduleResult-like dicts
    results = [
        {"scheduled": [1, 2], "deferred": [1], "accepted_risk": [], "escalations": [],
         "used_capacity": 2, "capacity": 5},
        {"scheduled": [1], "deferred": [], "accepted_risk": [], "escalations": [],
         "used_capacity": 1, "capacity": 5},
    ]
    assert scheduler_feasibility_rate(results) == 1.0

    # aggregation
    per_seed = pd.DataFrame({
        "strategy": ["proposed_full", "proposed_full", "random", "random"],
        "metric": ["precision@3"] * 4,
        "value": [0.6, 0.7, 0.3, 0.4],
        "seed": [1, 2, 1, 2],
    })
    agg = aggregate_metrics(per_seed)
    assert set(agg.columns) >= {"strategy", "metric", "mean", "std", "count"}
    prop_row = agg[agg["strategy"] == "proposed_full"].iloc[0]
    assert prop_row["mean"] == np.mean([0.6, 0.7])
    assert prop_row["count"] == 2
