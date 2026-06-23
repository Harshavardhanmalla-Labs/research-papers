"""Step-9 tests: aggregation, inference, post-run stop rules, figures, audit."""

from __future__ import annotations

import csv
import json
import pathlib

import pandas as pd
import pytest

from paper2_runtime import aggregate as agg
from paper2_runtime import figures as figs
from paper2_runtime import inference as inf
from paper2_runtime import post_run_stop_rules as prr
from paper2_runtime import step9_audit as s9a

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _make_tiny_primary_csv(dirpath, batch_id, *, cells, n_seeds=30,
                            strategy="epss_only", weight_vector="na",
                            capacity_ratio="0.01", blackout_policy="primary",
                            ablation="full", missing_witness=0):
    """Write a tiny per_seed_metrics.csv with the canonical schema."""
    dirpath.mkdir(parents=True, exist_ok=True)
    csv_p = dirpath / "per_seed_metrics.csv"
    fields = [
        "batch_id", "cell_id", "seed", "freeze_witness_id",
        "strategy", "weight_vector", "capacity_ratio", "blackout_policy",
        "approver_policy", "label_source", "epss_era", "catalog_strictness",
        "ablation", "t0_window_set", "metric", "value",
    ]
    metrics = ("ehd_absolute", "capacity_efficiency", "scheduler_feasibility",
               "scheduled_count_total", "n_pairs_total", "n_t0_windows")
    with csv_p.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        row_i = 0
        for c in cells:
            for seed in range(1, n_seeds + 1):
                for m_idx, metric in enumerate(metrics):
                    row_i += 1
                    val = {
                        "ehd_absolute": 1000.0 + (10.0 if c == "alt" else 0.0) + 0.1 * seed,
                        "capacity_efficiency": 0.01, "scheduler_feasibility": 1.0,
                        "scheduled_count_total": 100.0, "n_pairs_total": 10000.0,
                        "n_t0_windows": 18.0,
                    }[metric]
                    w.writerow({
                        "batch_id": batch_id, "cell_id": c, "seed": seed,
                        "freeze_witness_id": "" if row_i <= missing_witness else "wit-abc",
                        "strategy": strategy, "weight_vector": weight_vector,
                        "capacity_ratio": capacity_ratio,
                        "blackout_policy": blackout_policy,
                        "approver_policy": "A", "label_source": "label_a_kev_only",
                        "epss_era": "v3", "catalog_strictness": "cpe_exact_existing31",
                        "ablation": ablation, "t0_window_set": "monthly_18_2023_09_to_2025_02",
                        "metric": metric, "value": val,
                    })
    # Minimal stop_rule_evaluation.json (gate reads triggered ids).
    (dirpath / "stop_rule_evaluation.json").write_text(
        json.dumps({"triggered_rules": [{"rule_id": "K1"}, {"rule_id": "S-A"},
                                         {"rule_id": "K3"}]}),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def test_aggregation_validates_8640_rows():
    # Live test on real primary data: must hit the 8,640 row count exactly.
    raw = agg.load_primary_metric_rows()
    agg.validate_primary_rows(raw)
    assert len(raw) == agg.EXPECTED_PRIMARY_METRIC_ROWS == 8640


def test_aggregation_fails_when_witness_missing(tmp_path, monkeypatch):
    rd = tmp_path / "results"
    for bid in agg.STEP8_ALLOWED_BATCHES:
        _make_tiny_primary_csv(rd / bid, bid, cells=["c1"], n_seeds=30,
                                missing_witness=(2 if bid == "B-primary-blackout" else 0))
    monkeypatch.setattr(agg, "PRIMARY_RESULTS_DIR", rd)
    raw = agg.load_primary_metric_rows(rd)
    with pytest.raises(agg.AggregationError):
        agg.validate_primary_rows(raw)


def test_aggregation_fails_when_rows_count_wrong(tmp_path, monkeypatch):
    rd = tmp_path / "results"
    for bid in agg.STEP8_ALLOWED_BATCHES:
        _make_tiny_primary_csv(rd / bid, bid, cells=["c1"], n_seeds=29)  # too few
    raw = agg.load_primary_metric_rows(rd)
    with pytest.raises(agg.AggregationError):
        agg.validate_primary_rows(raw)


def test_aggregation_refuses_paper1_tables_dir():
    with pytest.raises(ValueError):
        agg.write_aggregation_outputs(tables_dir="paper/tables")


def test_delta_vs_epss_uses_correct_baseline():
    raw = agg.load_primary_metric_rows()
    agg.validate_primary_rows(raw)
    per_seed = agg.pivot_to_per_seed(raw)
    delta = agg.compute_paired_delta_vs_baseline(per_seed)
    assert (delta["baseline_strategy"] == "epss_only").all()
    # epss_only itself is excluded from delta.
    assert "epss_only" not in delta["strategy"].unique() or (
        delta[delta["strategy"] == "epss_only"]["delta_ehd_mean"].abs().max() < 1e-9
    )


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------


def test_inference_drops_diagnostic_metric_compatibility():
    """SM-5 diagnostic-only metrics are not used as the primary metric here, but
    the inference policy module exposes the same set used by SM-5 enforcement."""
    from paper2_runtime.inference_policy import DIAGNOSTIC_METRICS
    assert "precision_at_k" in DIAGNOSTIC_METRICS
    assert "kev_deadline_breach_rate" in DIAGNOSTIC_METRICS


def test_inference_runs_B1_family_on_real_data():
    raw = agg.load_primary_metric_rows()
    agg.validate_primary_rows(raw)
    per_seed = agg.pivot_to_per_seed(raw)
    records = inf.run_B1_family(per_seed)
    assert len(records) > 0
    statuses = {r["inference_status"] for r in records}
    assert statuses <= {"allowed", "dropped", "descriptive_only", "diagnostic_only"}
    # Every record carries the SM-4 guardrail field.
    for r in records:
        assert "interpretation_guardrail" in r


def test_inference_drops_degenerate_via_SM1(tmp_path, monkeypatch):
    # Build a per-seed frame where two cells have identical EHD across seeds.
    df = pd.DataFrame([
        {"cell_id": "X", "seed": s, "strategy": "epss_only", "weight_vector": "na",
         "capacity_ratio": "0.01", "blackout_policy": "primary", "approver_policy": "A",
         "ablation": "full", "ehd_absolute": 100.0, "batch_id": "B-primary-primary"}
        for s in range(1, 31)
    ] + [
        {"cell_id": "Y", "seed": s, "strategy": "random", "weight_vector": "na",
         "capacity_ratio": "0.01", "blackout_policy": "primary", "approver_policy": "A",
         "ablation": "full", "ehd_absolute": 100.0, "batch_id": "B-primary-primary"}
        for s in range(1, 31)
    ])
    records = inf.run_B1_family(df)
    dropped = [r for r in records if r["inference_status"] == "dropped"]
    assert any("SM-1" in r["drop_reason"] for r in dropped)


def test_inference_SM4_descriptive_when_ci_overlaps_zero():
    # Construct paired diffs with mean near 0 -> CI overlaps zero -> SM-4 guardrail.
    guardrail = inf._interpretation_guardrail(ci_low=-100.0, ci_high=100.0, holm_p=0.001)
    assert "descriptive" in guardrail


def test_inference_outputs_written(tmp_path, monkeypatch):
    raw = agg.load_primary_metric_rows()
    agg.validate_primary_rows(raw)
    per_seed = agg.pivot_to_per_seed(raw)
    out = tmp_path / "inference"
    inf.write_inference_outputs(inference_dir=out, per_seed=per_seed)
    assert (out / "inference_B1_delta_vs_epss.csv").exists()
    assert (out / "inference_C1_weight_family.csv").exists()
    assert (out / "inference_C2_capacity.csv").exists()
    assert (out / "inference_C3_blackout.csv").exists()
    assert (out / "inference_C4_feature_ablation.csv").exists()
    assert (out / "inference_policy_drops.csv").exists()


# ---------------------------------------------------------------------------
# Post-run stop rules
# ---------------------------------------------------------------------------


def test_K7_is_skipped_in_step9():
    res = prr.evaluate_K7()
    assert res["evaluated"] is False
    assert res["status"] == "SKIPPED"
    assert "rationale" in res


def test_K2_and_K8_evaluate_on_real_data(tmp_path):
    raw = agg.load_primary_metric_rows()
    agg.validate_primary_rows(raw)
    per_seed = agg.pivot_to_per_seed(raw)
    out = prr.write_post_run_outputs(
        tables_dir=tmp_path / "tables",
        audit_json=tmp_path / "audit" / "post_run.json",
        per_seed=per_seed,
    )
    for k in ("csv", "md", "audit_json"):
        assert out[k].exists(), k
    audit = json.loads(out["audit_json"].read_text())
    assert audit["K2"]["evaluated"] is True
    assert audit["K7"]["status"] == "SKIPPED"
    assert audit["K8"]["evaluated"] is True


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def test_no_seaborn_import():
    src = (REPO_ROOT / "paper2_runtime" / "figures.py").read_text()
    assert "import seaborn" not in src
    assert "from seaborn" not in src
    assert "import sns" not in src


def test_figures_generated_and_non_empty(tmp_path):
    raw = agg.load_primary_metric_rows()
    agg.validate_primary_rows(raw)
    per_seed = agg.pivot_to_per_seed(raw)
    out = tmp_path / "figures"
    written = figs.generate_all_figures(figures_dir=out, per_seed=per_seed)
    # 7 figures × (PNG + PDF) = 14 files; each must be > 0 bytes.
    for k, paths in written.items():
        for p in paths:
            assert p.exists() and p.stat().st_size > 0, (k, p)


def test_figures_refuse_paper1_output_dir():
    raw = agg.load_primary_metric_rows()
    agg.validate_primary_rows(raw)
    per_seed = agg.pivot_to_per_seed(raw)
    with pytest.raises(ValueError):
        figs.generate_all_figures(figures_dir="paper/figures", per_seed=per_seed)


# ---------------------------------------------------------------------------
# Step-9 audit artefact
# ---------------------------------------------------------------------------


def test_step9_audit_lists_generated_artifacts(tmp_path, monkeypatch):
    # Use real primary outputs; redirect step9 audit to tmp.
    raw = agg.load_primary_metric_rows()
    agg.validate_primary_rows(raw)
    per_seed = agg.pivot_to_per_seed(raw)
    tables = agg.write_aggregation_outputs(tables_dir=tmp_path / "tables")
    inference = inf.write_inference_outputs(
        inference_dir=tmp_path / "tables" / "inference", per_seed=per_seed,
    )
    post_run = prr.write_post_run_outputs(
        tables_dir=tmp_path / "tables",
        audit_json=tmp_path / "audit" / "post_run.json", per_seed=per_seed,
    )
    figures = figs.generate_all_figures(figures_dir=tmp_path / "figures", per_seed=per_seed)
    audit = s9a.build_step9_audit(
        tables_written=tables, inference_written=inference,
        figures_written=figures, post_run_written=post_run,
        primary_complete_json=REPO_ROOT / "paper2" / "audit" / "primary_complete.json",
    )
    assert audit["primary_complete_status"] == "PRIMARY_COMPLETE_VALID"
    assert len(audit["tables_generated"]) > 0
    assert len(audit["figures_generated"]) > 0
    assert audit["post_run_stop_rules_evaluated"] == ["K2", "K7", "K8"]
    j, m = s9a.write_step9_audit(
        audit, json_path=tmp_path / "step9.json", md_path=tmp_path / "step9.md",
    )
    assert j.exists()
    assert m.exists()


def test_step9_audit_refuses_paper1_paths(tmp_path):
    """We rely on aggregate / inference / figures refusing paper/ paths upstream."""
    with pytest.raises(ValueError):
        agg.write_aggregation_outputs(tables_dir="paper/tables")
    with pytest.raises(ValueError):
        inf.write_inference_outputs(inference_dir="paper/tables/inference")
