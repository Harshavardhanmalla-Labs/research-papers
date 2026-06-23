"""Experiment runners (Phase 11+).

Phase 11 ships only a tiny, deterministic end-to-end *smoke* runner that
wires the full pipeline (synthetic fleet -> toy vulnerabilities -> pairs ->
labels -> split -> features -> ranking strategies -> scheduler -> metrics ->
per-seed metric frame -> stats validation) on bundled toy fixtures, with no
live feeds. It is a pipeline verification, not a research result. Primary,
robustness, and sensitivity runners arrive in later phases.
"""

from paper1.experiments.common import (
    ExperimentManifest,
    collect_artifact_versions,
    dataframe_to_parquet_or_csv,
    ensure_result_dirs,
    load_manifest,
    stable_config_sha,
    validate_audit_logs,
    validate_strategy_outputs,
    write_manifest,
)
from paper1.experiments.inspect import (
    InspectionIssue,
    InspectionReport,
    compare_primary_runs,
    freeze_primary_results,
    inspect_primary_output,
    summarize_primary_output,
    verify_freeze_manifest,
)
from paper1.experiments.primary import (
    PrimaryRunConfig,
    checkpoint_exists,
    checkpoint_path,
    clear_checkpoint,
    estimate_primary_runtime,
    load_primary_config,
    make_primary_output_layout,
    plan_primary_run,
    read_checkpoint,
    run_primary_confirmed,
    run_primary_dryrun,
    run_primary_experiment,
    validate_primary_inputs,
    write_checkpoint,
)
from paper1.experiments.smoke import run_smoke_experiment, run_smoke_seed

__all__ = [
    "ExperimentManifest",
    "InspectionIssue",
    "InspectionReport",
    "PrimaryRunConfig",
    "checkpoint_exists",
    "checkpoint_path",
    "clear_checkpoint",
    "collect_artifact_versions",
    "compare_primary_runs",
    "dataframe_to_parquet_or_csv",
    "ensure_result_dirs",
    "estimate_primary_runtime",
    "freeze_primary_results",
    "inspect_primary_output",
    "load_manifest",
    "load_primary_config",
    "make_primary_output_layout",
    "plan_primary_run",
    "read_checkpoint",
    "run_primary_confirmed",
    "run_primary_dryrun",
    "run_primary_experiment",
    "run_smoke_experiment",
    "run_smoke_seed",
    "stable_config_sha",
    "summarize_primary_output",
    "validate_audit_logs",
    "validate_primary_inputs",
    "validate_strategy_outputs",
    "verify_freeze_manifest",
    "write_checkpoint",
    "write_manifest",
]
