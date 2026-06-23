#!/usr/bin/env python3
"""Step-9 orchestrator: aggregate + inference + post-run stop rules + figures + audit."""

from __future__ import annotations

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from paper2_runtime.aggregate import (  # noqa: E402
    PRIMARY_RESULTS_DIR,
    TABLES_DIR,
    load_primary_metric_rows,
    pivot_to_per_seed,
    validate_primary_rows,
    write_aggregation_outputs,
)
from paper2_runtime.figures import FIGURES_DIR, generate_all_figures  # noqa: E402
from paper2_runtime.inference import INFERENCE_DIR, write_inference_outputs  # noqa: E402
from paper2_runtime.post_run_stop_rules import (  # noqa: E402
    write_post_run_outputs,
)
from paper2_runtime.step9_audit import (  # noqa: E402
    STEP9_AUDIT_JSON,
    STEP9_AUDIT_MD,
    build_step9_audit,
    write_step9_audit,
)

PRIMARY_COMPLETE_JSON = _REPO_ROOT / "paper2" / "audit" / "primary_complete.json"


def main() -> int:
    if not PRIMARY_COMPLETE_JSON.exists():
        print(f"ERROR: missing {PRIMARY_COMPLETE_JSON}", file=sys.stderr)
        return 1
    print("=== Step 9 orchestrator ===")
    print(f"  primary_complete: {PRIMARY_COMPLETE_JSON}")
    print(f"  tables_dir: {TABLES_DIR}")
    print(f"  inference_dir: {INFERENCE_DIR}")
    print(f"  figures_dir: {FIGURES_DIR}")

    raw = load_primary_metric_rows()
    validate_primary_rows(raw)
    per_seed = pivot_to_per_seed(raw)
    print(f"  loaded {len(raw)} rows; pivoted to {len(per_seed)} per-(cell, seed) rows")

    tables = write_aggregation_outputs(primary_results_root=PRIMARY_RESULTS_DIR)
    print(f"  aggregation: {sum(len(v) for v in tables.values())} files")

    inference = write_inference_outputs(per_seed=per_seed)
    print(f"  inference:   {sum(len(v) for v in inference.values())} files")

    post_run = write_post_run_outputs(per_seed=per_seed)
    print(f"  post_run:    {len(post_run)} files")

    figures = generate_all_figures(per_seed=per_seed)
    print(f"  figures:     {sum(len(v) for v in figures.values())} files")

    audit = build_step9_audit(
        tables_written=tables, inference_written=inference,
        figures_written=figures, post_run_written=post_run,
        primary_complete_json=PRIMARY_COMPLETE_JSON,
    )
    j, m = write_step9_audit(audit, STEP9_AUDIT_JSON, STEP9_AUDIT_MD)
    print(f"  audit json:  {j}")
    print(f"  audit md:    {m}")
    print(f"  Step 10 drafting allowed: {audit['step10_manuscript_drafting_allowed']}")
    return 0 if audit["step10_manuscript_drafting_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
