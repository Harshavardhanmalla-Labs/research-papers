"""Tests for paper2_runtime.inference_policy — F4 SM-1/3/5 shim."""

from __future__ import annotations

from paper2_runtime.inference_policy import (
    DIAGNOSTIC_METRICS,
    diagnostic_only,
    enforce_sm1_degeneracy,
    enforce_sm3_oracle_disabled,
    enforce_sm5_no_significance_for_diagnostics,
    should_run_wilcoxon,
)


def test_kev_first_pair_dropped_for_inference():
    assert should_run_wilcoxon("kev_first__vs__epss_only", {"n_pairs": 30}) is False


def test_kev_first_pair_dropped_via_sm1_degeneracy_when_std_zero():
    # n=30 paired Δs identically zero -> std=0 -> SM-1 drops the test.
    diffs = [0.0] * 30
    assert enforce_sm1_degeneracy(diffs) == "dropped"
    # The Wilcoxon gate also drops via the paired_delta_std=0 check.
    assert should_run_wilcoxon(
        "random__vs__epss_only", {"n_pairs": 30, "paired_delta_std": 0.0}
    ) is False


def test_sm1_allows_non_degenerate_diffs():
    diffs = [1.0, -2.0, 0.5, -0.5, 0.0] * 6
    assert enforce_sm1_degeneracy(diffs) == "allowed"


def test_oracle_inference_disabled_for_CLM_B3():
    assert enforce_sm3_oracle_disabled("CLM-B3") == "disabled"
    assert enforce_sm3_oracle_disabled("fraction_of_oracle") == "disabled"
    assert enforce_sm3_oracle_disabled("oracle__vs__epss_only") == "disabled"


def test_oracle_pair_gates_off_wilcoxon():
    assert should_run_wilcoxon("oracle__vs__epss_only", {"n_pairs": 30}) is False


def test_precision_recall_ndcg_diagnostic_only():
    for m in ("precision_at_k", "recall_at_k", "ndcg_at_k"):
        assert diagnostic_only(m)


def test_kev_breach_rate_diagnostic_only():
    assert diagnostic_only("kev_deadline_breach_rate")
    assert diagnostic_only("kev_remediation_latency")


def test_diagnostic_metric_blocks_wilcoxon():
    assert should_run_wilcoxon(
        "random__vs__epss_only",
        {"n_pairs": 30, "metric_name": "precision_at_k"},
    ) is False


def test_sm5_rejects_significance_near_diagnostic_metric():
    bad = "precision_at_k was significant under Holm with p = 0.04."
    assert enforce_sm5_no_significance_for_diagnostics(bad) == "rejected"

    bad_kev = "kev_deadline_breach_rate showed a significant decrease (p<0.01)."
    assert enforce_sm5_no_significance_for_diagnostics(bad_kev) == "rejected"


def test_sm5_accepts_neutral_text():
    ok = "EHD ΔEHD was small with CI [-100, +200]."
    assert enforce_sm5_no_significance_for_diagnostics(ok) == "ok"


def test_sm5_accepts_bare_metric_name():
    # Reporting the metric name in an appendix without significance language is OK.
    assert enforce_sm5_no_significance_for_diagnostics("precision_at_k") == "ok"


def test_diagnostic_metrics_set_contains_expected():
    for m in (
        "precision_at_k", "recall_at_k", "ndcg_at_k",
        "kev_deadline_breach_rate", "risk_acceptance_rate",
        "imputation_rate",
    ):
        assert m in DIAGNOSTIC_METRICS
