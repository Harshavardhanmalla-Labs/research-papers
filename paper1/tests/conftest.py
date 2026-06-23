"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest

from paper1 import __framework_version__
from paper1.utils.io import atomic_write_json

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIGS_DIR = REPO_ROOT / "configs"

# Metric names emitted per (seed, strategy) by the runner (11 metrics).
_TINY_METRICS = [
    "precision_at_k",
    "recall_at_k",
    "ndcg_at_k",
    "ehd_absolute",
    "kev_breach_rate",
    "capacity_efficiency",
    "scheduler_feasibility",
    "risk_acceptance_rate",
    "audit_hash_chain_valid",
    "audit_record_count",
    "scheduled_count",
]
# Base EHD levels: oracle < proposed_full < epss_only < random (lower = better).
_TINY_EHD = {"random": 1000.0, "epss_only": 900.0, "proposed_full": 850.0, "oracle": 800.0}


def build_tiny_frozen_output(root: Path, *, seeds=(1, 2, 3), capacity: int = 10) -> Path:
    """Write a small *synthetic* frozen primary output and freeze it.

    Produces the three metric frames + manifest + summary using the real
    EEHDA reporting helper, then writes a FREEZE_MANIFEST. No pipeline is run
    and no result is interpreted; this only exercises the reporting layer.
    """
    from paper1.evaluation.eehda import eehda_report
    from paper1.experiments.inspect import freeze_primary_results

    strategies = list(_TINY_EHD)
    rows: list[dict] = []
    for s in seeds:
        for strat in strategies:
            base = _TINY_EHD[strat]
            for metric in _TINY_METRICS:
                if metric == "ehd_absolute":
                    value = base + s  # tiny per-seed jitter; ordering preserved
                elif metric == "scheduled_count":
                    value = float(capacity - 1)  # within capacity
                elif metric == "audit_hash_chain_valid":
                    value = 1.0
                elif metric == "audit_record_count":
                    value = 42.0
                elif metric in ("precision_at_k", "recall_at_k", "ndcg_at_k"):
                    value = 0.5
                elif metric == "scheduler_feasibility":
                    value = 1.0
                else:  # kev_breach_rate, capacity_efficiency, risk_acceptance_rate
                    value = 0.1
                rows.append({"seed": s, "strategy": strat, "metric": metric, "value": value})
    per_seed = pd.DataFrame(rows, columns=["seed", "strategy", "metric", "value"])

    aggregated = (
        per_seed.groupby(["strategy", "metric"])["value"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .sort_values(["strategy", "metric"])
        .reset_index(drop=True)
    )

    ehd_mean = (
        per_seed[per_seed["metric"] == "ehd_absolute"]
        .groupby("strategy")["value"]
        .mean()
        .to_dict()
    )
    eehda = eehda_report(ehd_mean)

    metrics_dir = root / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    per_seed.to_csv(metrics_dir / "per_seed_metrics.csv", index=False)
    aggregated.to_csv(metrics_dir / "aggregated_metrics.csv", index=False)
    eehda.to_csv(metrics_dir / "eehda_report.csv", index=False)
    atomic_write_json(
        root / "manifest.json",
        {
            "config_name": "tiny_synthetic",
            "config_sha": "0" * 64,
            "code_version": __framework_version__,
            "created_at": "2026-05-27T00:00:00+00:00",
            "seeds": list(seeds),
            "strategies": strategies,
            "output_dir": str(root),
            "artifact_versions": {},
            "notes": "synthetic test fixture; not a result",
        },
    )
    (root / "summary.md").write_text("# tiny synthetic\n", encoding="utf-8")

    freeze_primary_results(root)
    return root


@pytest.fixture
def tiny_frozen_dir(tmp_path) -> Path:
    """A small, frozen, synthetic primary output for reporting tests."""
    return build_tiny_frozen_output(tmp_path / "frozen", seeds=(1, 2, 3), capacity=10)


@pytest.fixture
def framework_version() -> str:
    return __framework_version__


@pytest.fixture
def configs_dir() -> Path:
    return CONFIGS_DIR


@pytest.fixture
def utc_dt() -> datetime:
    return datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_date() -> date:
    return date(2026, 5, 26)


@pytest.fixture
def sample_score_kwargs(utc_dt):
    """Kwargs for a valid `decision_type='score'` AuditDecisionRecord (minus hashes)."""
    return {
        "record_id": "ADR-score-1",
        "pair_id": "H-test:CVE-2025-12345",
        "window_id": "W-2026-22-tue",
        "decision_type": "score",
        "priority_score": 7.84,
        "feature_values": {
            "E": 0.873,
            "K": 1.0,
            "S": 0.91,
            "C": 0.81,
            "X": 0.75,
            "U": 0.66,
            "R": 0.40,
        },
        "feature_contributions": {
            "E": 1.74,
            "K": 2.0,
            "S": 0.91,
            "C": 1.62,
            "X": 1.50,
            "U": 0.66,
            "R": -0.40,
        },
        "weights_version": "w_logit-v1",
        "data_feed_versions": {
            "nvd": "2026-05-26",
            "epss": "2026-05-26",
            "kev": "2026-05-26",
        },
        "framework_version": "paper1-0.1.0-phase1",
        "created_at": utc_dt,
    }


@pytest.fixture
def sample_accept_risk_kwargs(utc_dt, sample_date):
    return {
        "record_id": "ADR-acceptrisk-1",
        "pair_id": "H-test:CVE-2025-99999",
        "window_id": "W-2026-22-tue",
        "decision_type": "accept_risk",
        "weights_version": "w_logit-v1",
        "data_feed_versions": {"nvd": "2026-05-26"},
        "framework_version": "paper1-0.1.0-phase1",
        "approver_id": "user:jane.doe",
        "risk_acceptance_reason": "Compensating control in place; remediation deferred.",
        "risk_acceptance_compensating_controls": ["network_isolation"],
        "risk_acceptance_expiration_date": sample_date,
        "risk_acceptance_review_trigger": "kev_addition",
        "risk_acceptance_approver_id": "user:senior.approver",
        "created_at": utc_dt,
    }
