"""Tests for scripts/paper2_claim_audit.py."""

from __future__ import annotations

import importlib.util
import pathlib

_SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "paper2_claim_audit.py"
spec = importlib.util.spec_from_file_location("paper2_claim_audit", _SCRIPT)
_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_module)
find_violations = _module.find_violations


def _has(violations, type_):
    return any(v["type"] == type_ for v in violations)


def test_audit_passes_on_safe_draft():
    text = (
        "We present a failure-aware gate. We report descriptive ΔEHD relative to "
        "EPSS. No production validation is claimed; the synthetic fleet is a "
        "Limitations item. Calibration was not attempted under the gate."
    )
    assert find_violations(text) == []


def test_audit_fails_on_outperforms():
    text = "Strategy X outperforms EPSS across cells."
    violations = find_violations(text)
    assert _has(violations, "always_forbidden")
    assert any("outperform" in v["phrase"].lower() for v in violations)


def test_audit_fails_on_superior():
    text = "Our approach is superior to all baselines."
    assert _has(find_violations(text), "always_forbidden")


def test_audit_fails_on_state_of_the_art():
    assert _has(find_violations("We achieve state-of-the-art results."), "always_forbidden")
    assert _has(find_violations("We achieve state of the art performance."), "always_forbidden")


def test_audit_allows_not_validated():
    """`validated` is OK when preceded by a negation token."""
    text = "The model is not validated; we do not claim production deployment-readiness."
    violations = find_violations(text)
    # Should not flag the negatable phrases here.
    assert not _has(violations, "negatable_phrase_unnegated")


def test_audit_fails_on_unnegated_validated():
    text = "The pipeline is validated against gold-standard data."
    assert _has(find_violations(text), "negatable_phrase_unnegated")


def test_audit_allows_no_production_validation():
    text = "We make no production validation claim in this work."
    violations = find_violations(text)
    assert not _has(violations, "negatable_phrase_unnegated")


def test_audit_fails_on_unnegated_production():
    text = "This pipeline is suitable for production deployment."
    assert _has(find_violations(text), "negatable_phrase_unnegated")


def test_audit_fails_on_government_deployment():
    assert _has(find_violations("Intended for government deployment."), "always_forbidden")


def test_audit_fails_on_compliance_achieved():
    assert _has(find_violations("Compliance achieved across audits."), "always_forbidden")


def test_audit_fails_on_calibrated_model_improves():
    text = "Our calibrated model improves ranking quality."
    assert _has(find_violations(text), "always_forbidden")


def test_audit_fails_on_learned_model():
    text = "We deploy a learned model trained on KEV labels."
    assert _has(find_violations(text), "always_forbidden")


def test_audit_fails_on_significant_near_precision():
    text = "We observed a significant change in precision_at_k across vectors."
    assert _has(find_violations(text), "significant_near_diagnostic")


def test_audit_fails_on_significant_near_recall():
    text = "Recall@k showed a significantly higher value under the prior."
    assert _has(find_violations(text), "significant_near_diagnostic")


def test_audit_fails_on_significant_near_kev_breach():
    text = "The kev breach rate decreased significantly under the prior."
    assert _has(find_violations(text), "significant_near_diagnostic")


def test_audit_allows_significant_far_from_diagnostic():
    text = (
        "We observed a significant ΔEHD descriptive observation; this is a "
        "primary-metric finding gated by SM-4."
    )
    assert not _has(find_violations(text), "significant_near_diagnostic")


def test_audit_fails_on_pair_count_as_sample_size():
    text = "The pair count of 8,640 is treated as the effective sample size."
    assert _has(find_violations(text), "pair_count_as_sample_size")


def test_audit_fails_on_pair_count_as_effective_N():
    text = "We use pair count as the effective N for power analysis."
    assert _has(find_violations(text), "pair_count_as_sample_size")


def test_audit_allows_pair_count_with_correction():
    text = (
        "We emphasise that pair count is not the calibration sample size; the "
        "effective N is unique positive CVE count."
    )
    # `pair count` is here, but with strong negation that it's NOT the sample size.
    # The audit flags pair_count near sample/effective N tokens because the
    # window is narrow; the manuscript can restate without the trigger phrase.
    # We accept that this snippet would be flagged and the manuscript avoids it.
    violations = find_violations(text)
    # This SHOULD flag — by design — to push authors to rephrase.
    assert _has(violations, "pair_count_as_sample_size")


def test_audit_fails_on_positive_calibration_claim():
    assert _has(find_violations("After calibration, the weights stabilise."),
                "positive_calibration_claim")
    assert _has(find_violations("The model was calibrated using public-feed labels."),
                "positive_calibration_claim")


def test_audit_allows_negated_calibration_claim():
    text = "Calibration was not attempted; the model was not calibrated due to sparse labels."
    violations = find_violations(text)
    assert not _has(violations, "positive_calibration_claim")


def test_audit_fails_on_context_priors_beat_epss():
    text = "Context-aware priors outperform EPSS at the central cell."
    assert _has(find_violations(text), "superiority_over_epss")


def test_audit_allows_descriptive_context_priors_below_epss():
    text = "Context-aware priors yield a lower EHD than EPSS at the central cell (descriptive)."
    violations = find_violations(text)
    assert not _has(violations, "superiority_over_epss")


def test_audit_main_returns_zero_on_pass(tmp_path):
    p = tmp_path / "ok.md"
    p.write_text("All claims are descriptive; no production validation.")
    assert _module.audit_file(p) == 0


def test_audit_main_returns_nonzero_on_fail(tmp_path):
    p = tmp_path / "bad.md"
    p.write_text("Our method outperforms all baselines.")
    assert _module.audit_file(p) == 1
