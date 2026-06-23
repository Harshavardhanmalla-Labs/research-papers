"""Audit-metric tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from paper1.audit.hash_chain import AuditLogger
from paper1.evaluation.audit_metrics import (
    audit_explanation_completeness,
    audit_record_count_by_type,
    hash_chain_validity,
    imputation_rate_per_feature,
)
from paper1.model.weights import FEATURE_COLUMNS


def _features(**over):
    base = dict.fromkeys(FEATURE_COLUMNS, 0.5)
    base.update(over)
    return base


def _contributions():
    return dict.fromkeys(FEATURE_COLUMNS, 0.1)


def _score_record(record_id, *, feature_values=None, contributions=None, imputed=None):
    return {
        "record_id": record_id,
        "pair_id": f"H:{record_id}",
        "window_id": "W-1",
        "decision_type": "score",
        "priority_score": 0.5,
        "feature_values": feature_values if feature_values is not None else _features(),
        "feature_contributions": contributions if contributions is not None else _contributions(),
        "weights_version": "w_logit-v1",
        "data_feed_versions": {"nvd": "2026-05-26"},
        "imputations_applied": imputed,
        "framework_version": "paper1-0.1.0",
    }


def test_completeness_one_for_complete_records():
    records = [_score_record("r1"), _score_record("r2")]
    assert audit_explanation_completeness(records) == 1.0


def test_incomplete_record_lowers_completeness():
    incomplete = _score_record("r2")
    incomplete["feature_values"] = {"E": 0.5}  # missing the rest
    records = [_score_record("r1"), incomplete]
    assert audit_explanation_completeness(records) == 0.5


def test_no_score_records_nan():
    records = [{"decision_type": "schedule", "pair_id": "H:1"}]
    assert np.isnan(audit_explanation_completeness(records))


def test_imputation_rate_hand_computed():
    records = [
        _score_record("r1", imputed=[{"feature": "E"}]),
        _score_record("r2", imputed=[{"feature": "E"}, {"feature": "S"}]),
        _score_record("r3", imputed=None),
    ]
    rates = imputation_rate_per_feature(records)
    assert rates["E"] == 2 / 3
    assert rates["S"] == 1 / 3
    assert rates["C"] == 0.0


def test_imputation_rate_accepts_string_items():
    records = [_score_record("r1", imputed=["E", "K"])]
    rates = imputation_rate_per_feature(records)
    assert rates["E"] == 1.0
    assert rates["K"] == 1.0


def test_count_by_type():
    records = [
        {"decision_type": "score", "pair_id": "a"},
        {"decision_type": "schedule", "pair_id": "b"},
        {"decision_type": "schedule", "pair_id": "c"},
        {"decision_type": "defer", "pair_id": "d"},
    ]
    counts = audit_record_count_by_type(records)
    assert counts == {"score": 1, "schedule": 2, "defer": 1}


def test_hash_chain_validity_true_and_tamper(tmp_path: Path):
    path = tmp_path / "audit.jsonl"
    logger = AuditLogger(path)
    logger.append(
        record_id="ADR-1", pair_id="H:1", window_id="W-1", decision_type="schedule",
        weights_version="w", data_feed_versions={}, framework_version="fv",
        created_at=datetime(2026, 5, 26, 12, 0, tzinfo=UTC),
    )
    logger.append(
        record_id="ADR-2", pair_id="H:2", window_id="W-1", decision_type="defer",
        weights_version="w", data_feed_versions={}, framework_version="fv",
        created_at=datetime(2026, 5, 26, 12, 0, tzinfo=UTC),
        approver_comments="BLACKOUT",
    )
    assert hash_chain_validity(path) is True

    lines = path.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    first["pair_id"] = "TAMPERED"
    lines[0] = json.dumps(first, sort_keys=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert hash_chain_validity(path) is False


def test_metrics_from_jsonl_path(tmp_path: Path):
    from paper1.utils.io import write_jsonl

    path = tmp_path / "records.jsonl"
    write_jsonl(path, [_score_record("r1"), _score_record("r2", imputed=[{"feature": "E"}])])
    assert audit_explanation_completeness(path) == 1.0
    assert imputation_rate_per_feature(path)["E"] == 0.5
