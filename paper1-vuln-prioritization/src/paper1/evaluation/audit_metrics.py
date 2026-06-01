"""Audit-trail metrics: explanation completeness, imputation rate, integrity."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from paper1.audit.hash_chain import verify_chain
from paper1.model.weights import FEATURE_COLUMNS
from paper1.utils.io import read_jsonl

__all__ = [
    "audit_explanation_completeness",
    "audit_record_count_by_type",
    "hash_chain_validity",
    "imputation_rate_per_feature",
]


def _normalize_records(audit_records: Any) -> list[dict[str, Any]]:
    if isinstance(audit_records, (str, Path)):
        return list(read_jsonl(audit_records))
    out: list[dict[str, Any]] = []
    for r in audit_records:
        if hasattr(r, "model_dump"):
            out.append(r.model_dump(mode="json"))
        elif isinstance(r, dict):
            out.append(r)
        else:
            raise TypeError(f"unsupported audit record type: {type(r).__name__}")
    return out


def _has_all_features(mapping: Any) -> bool:
    if not isinstance(mapping, dict):
        return False
    return all(f in mapping and mapping[f] is not None for f in FEATURE_COLUMNS)


def audit_explanation_completeness(audit_records: Any) -> float:
    """Fraction of score records with complete features/contributions/provenance."""
    records = _normalize_records(audit_records)
    score_records = [r for r in records if r.get("decision_type") == "score"]
    if not score_records:
        return np.nan
    complete = 0
    for r in score_records:
        if (
            _has_all_features(r.get("feature_values"))
            and _has_all_features(r.get("feature_contributions"))
            and r.get("weights_version")
            and r.get("framework_version")
            and isinstance(r.get("data_feed_versions"), dict)
        ):
            complete += 1
    return complete / len(score_records)


def imputation_rate_per_feature(audit_records: Any) -> dict[str, float]:
    """Per-feature fraction of score records where that feature was imputed."""
    records = _normalize_records(audit_records)
    score_records = [r for r in records if r.get("decision_type") == "score"]
    counts: Counter[str] = Counter()
    n = len(score_records)
    for r in score_records:
        applied = r.get("imputations_applied") or []
        for item in applied:
            feat = item.get("feature") if isinstance(item, dict) else str(item)
            if feat in FEATURE_COLUMNS:
                counts[feat] += 1
    if n == 0:
        return {f: np.nan for f in FEATURE_COLUMNS}
    return {f: counts.get(f, 0) / n for f in FEATURE_COLUMNS}


def hash_chain_validity(audit_log_path: str | Path) -> bool:
    """Whether the on-disk audit log's hash chain verifies."""
    ok, _issues = verify_chain(audit_log_path)
    return ok


def audit_record_count_by_type(audit_records: Any) -> dict[str, int]:
    records = _normalize_records(audit_records)
    counts: Counter[str] = Counter()
    for r in records:
        counts[str(r.get("decision_type"))] += 1
    return dict(counts)
