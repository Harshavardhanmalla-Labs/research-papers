"""Tests for paper2_runtime.stop_rules — F5 registry loader + static evaluator."""

from __future__ import annotations

from paper2_runtime.stop_rules import (
    ALLOWED_ENFORCEMENT,
    ALLOWED_SEVERITY,
    REQUIRED_FIELDS,
    evaluate_known_static_rules,
    load_stop_rules,
    write_stop_rule_evaluation,
)


def test_registry_loads_and_validates_closed_set():
    rules = load_stop_rules()
    assert len(rules) >= 25, "expected ~25 stop rules (K1-K8 + S-* + SM-*)"
    ids = {r.rule_id for r in rules}
    # Canonical K-rules present.
    for rid in ("K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8"):
        assert rid in ids, rid
    # F3 S-rules present (sample).
    for rid in ("S-A", "S-B1", "S-B3", "S-C1", "S-C2", "S-C3", "S-C4", "S-D1", "S-G1"):
        assert rid in ids, rid
    # F4 SM-rules present.
    for rid in ("SM-1", "SM-2", "SM-3", "SM-4", "SM-5", "SM-6"):
        assert rid in ids, rid
    # All rules carry required fields.
    for r in rules:
        for f in REQUIRED_FIELDS:
            assert hasattr(r, f), (r.rule_id, f)
    # All enforcement / severity values are in the closed sets advertised by the YAML.
    assert ALLOWED_ENFORCEMENT
    assert ALLOWED_SEVERITY
    for r in rules:
        assert r.enforcement in ALLOWED_ENFORCEMENT, (r.rule_id, r.enforcement)
        assert r.severity in ALLOWED_SEVERITY, (r.rule_id, r.severity)


def test_K1_triggers_for_step_3_8_measurement():
    triggered = evaluate_known_static_rules({"unique_positive_distinct_cves": 7})
    ids = {t.rule_id for t in triggered}
    assert "K1" in ids
    assert "K3" in ids  # OR branch (unique_positive < 20)
    assert "S-A" in ids  # mirrors K1


def test_K3_per_window_share_branch():
    # 0 windows > 75% with < 3 positives but unique below threshold also triggers.
    pcs = [0] * 14 + [1, 2, 0, 0]  # 18 windows; all < 3
    triggered = evaluate_known_static_rules({
        "unique_positive_distinct_cves": 1000,  # high; OR branch off
        "per_window_positive_counts": pcs,
    })
    ids = {t.rule_id for t in triggered}
    assert "K1" not in ids
    assert "S-A" not in ids
    assert "K3" in ids  # share-of-windows branch


def test_K6_triggers_when_freeze_status_false():
    triggered = evaluate_known_static_rules({"freeze_status_before": "FAIL"})
    assert any(t.rule_id == "K6" for t in triggered)


def test_K5_K5a_trigger_on_leakage_warning():
    triggered = evaluate_known_static_rules({"leakage_warning_count": 1})
    ids = {t.rule_id for t in triggered}
    assert "K5" in ids
    assert "K5.a" in ids


def test_write_stop_rule_evaluation_creates_all_artefacts(tmp_path):
    triggered = evaluate_known_static_rules({"unique_positive_distinct_cves": 7})
    paths = write_stop_rule_evaluation(tmp_path, triggered, {"unique_positive_distinct_cves": 7})
    for k in ("stop_rule_evaluation.json", "stop_rule_evaluation.md",
              "triggered_rules.csv", "excluded_cells.csv", "downgraded_claims.csv"):
        assert (tmp_path / k).exists(), k
        assert paths[k].exists()


def test_write_refuses_paper1_paths(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        write_stop_rule_evaluation("results/primary_full_v1/x", [], {})


def test_no_unknown_enforcement_or_severity_values():
    rules = load_stop_rules()
    for r in rules:
        assert r.enforcement in ALLOWED_ENFORCEMENT
        assert r.severity in ALLOWED_SEVERITY
