.PHONY: install install-dev test lint format clean compile help \
        fetch-nvd fetch-epss fetch-kev fetch-poc validate-snapshots \
        synthetic-smoke pairs-smoke score-smoke calibrate-smoke gbt-smoke \
        scheduler-smoke metrics-smoke stats-smoke experiment-smoke primary-dryrun \
        primary-plan primary-one-seed primary-three-seeds \
        inspect-primary freeze-primary verify-primary-freeze primary-report \
        paper2-feasibility-probe paper2-multit0-probe \
        paper2-runtime-test paper2-verify-freeze paper2-plan \
        paper2-pilot-B-pilot-primary paper2-pilot-smoke-status \
        paper2-pilot-B-pilot-primary-full paper2-pilot-B-pilot-capacity \
        paper2-pilot-B-pilot-blackout paper2-pilot-B-pilot-ablation \
        paper2-pilot-full paper2-pilot-gate \
        paper2-primary-B-primary-primary paper2-primary-B-primary-capacity \
        paper2-primary-B-primary-blackout paper2-primary-B-primary-ablation \
        paper2-primary-full paper2-primary-status paper2-primary-complete \
        paper2-step9

PYTHON ?= python3.11
PIP    ?= $(PYTHON) -m pip

# Date defaults used by the fetch targets; override on the command line:
#   make fetch-epss START=2025-01-01 END=2025-01-31
START ?= 2024-06-01
END   ?= 2024-06-30
AS_OF ?= 2024-06-30
OUT   ?= data/snapshots

help:
	@echo "Targets:"
	@echo "  install              Install paper1 (runtime deps only)"
	@echo "  install-dev          Install paper1 with dev deps"
	@echo "  test                 Run pytest"
	@echo "  lint                 Run ruff lint"
	@echo "  format               Run ruff format"
	@echo "  compile              Byte-compile src/ + scripts/"
	@echo "  clean                Remove caches and build artifacts"
	@echo "  fetch-nvd            Fetch NVD CVEs into snapshot cache"
	@echo "  fetch-epss           Fetch daily EPSS snapshots (resumable)"
	@echo "  fetch-kev            Fetch CISA KEV catalog"
	@echo "  fetch-poc            Fetch ExploitDB index (license-gated)"
	@echo "  validate-snapshots   Verify manifest SHA-256 checksums"

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check src tests

format:
	$(PYTHON) -m ruff format src tests

compile:
	$(PYTHON) -m compileall -q src scripts

fetch-nvd:
	$(PYTHON) scripts/fetch_nvd.py --start $(START) --end $(END) --out $(OUT)

fetch-epss:
	$(PYTHON) scripts/fetch_epss.py --start $(START) --end $(END) --out $(OUT)

fetch-kev:
	$(PYTHON) scripts/fetch_kev.py --as-of $(AS_OF) --out $(OUT)

fetch-poc:
	$(PYTHON) scripts/fetch_poc.py --as-of $(AS_OF) --out $(OUT)

validate-snapshots:
	$(PYTHON) scripts/validate_snapshots.py --manifest $(OUT)/MANIFEST.json

synthetic-smoke:
	$(PYTHON) -c "from paper1.synthetic import generate_synthetic_fleet_bundle; \
b = generate_synthetic_fleet_bundle(fleet_size=100, seed=1, t0='2026-05-31'); \
from collections import Counter; \
print('hosts:', len(b['hosts'])); \
print('criticality:', len(b['criticality'])); \
print('by role:', dict(Counter(h.role for h in b['hosts'])))"

pairs-smoke:
	$(PYTHON) scripts/build_pairs_smoke.py --size 100 --seed 1 --t0 2025-06-01 --h-days 30

score-smoke:
	$(PYTHON) scripts/score_pairs_smoke.py

calibrate-smoke:
	$(PYTHON) scripts/calibrate_weights_smoke.py

gbt-smoke:
	$(PYTHON) scripts/gbt_smoke.py

scheduler-smoke:
	$(PYTHON) scripts/scheduler_smoke.py

metrics-smoke:
	$(PYTHON) scripts/metrics_smoke.py

stats-smoke:
	$(PYTHON) scripts/stats_smoke.py

experiment-smoke:
	$(PYTHON) scripts/run_smoke_experiment.py --config configs/experiment_smoke.yaml

primary-dryrun:
	$(PYTHON) scripts/run_primary_experiment.py --config configs/primary_dryrun.yaml --dry-run --max-seeds 1

# Controlled primary execution. There is intentionally NO full-30-seed target.
# Safe order: primary-plan -> primary-one-seed -> inspect -> primary-three-seeds.
primary-plan:
	$(PYTHON) scripts/run_primary_experiment.py --config configs/primary_full_template.yaml --plan --max-seeds 1

primary-one-seed:
	$(PYTHON) scripts/run_primary_experiment.py --config configs/primary_full_template.yaml --confirm-full-run --max-seeds 1

primary-three-seeds:
	$(PYTHON) scripts/run_primary_experiment.py --config configs/primary_full_template.yaml --confirm-full-run --max-seeds 3

inspect-primary:
	$(PYTHON) scripts/inspect_primary_results.py --output results/primary_full_v1 --strict

freeze-primary:
	$(PYTHON) scripts/inspect_primary_results.py --output results/primary_full_v1 --strict --freeze

verify-primary-freeze:
	$(PYTHON) scripts/inspect_primary_results.py --output results/primary_full_v1 --verify-freeze

primary-report:
	$(PYTHON) scripts/generate_primary_report.py --output results/primary_full_v1 --verify-freeze

paper2-feasibility-probe:
	$(PYTHON) scripts/paper2_feasibility_probe.py \
	  --start-date 2023-06-01 \
	  --end-date 2024-09-30 \
	  --t0 2024-09-01 \
	  --h-days 30 \
	  --fleet-size 500 \
	  --seed 20260601 \
	  --out paper2/feasibility/probe_v1 \
	  --min-positive-cves 50

# --- Paper 2 runtime (Step 5: implementation contract loaders + tests only) ---
# These targets must never execute experiment cells.
paper2-runtime-test:
	$(PYTHON) -m pytest tests/test_paper1_weights_locked.py \
	  tests/test_paper2_stop_rules.py tests/test_paper2_freeze_invariant.py \
	  tests/test_paper2_cell_loader.py tests/test_paper2_batch_loader.py \
	  tests/test_paper2_inference_policy.py tests/test_paper2_run_planner.py -q

paper2-verify-freeze:
	$(MAKE) verify-primary-freeze PYTHON=$(PYTHON)

paper2-plan:
	$(PYTHON) -m paper2_runtime.run_planner

# Step 6: launch ONE pilot batch (B-pilot-primary) in smoke mode only.
paper2-pilot-B-pilot-primary:
	$(PYTHON) scripts/paper2_run_pilot_batch.py --batch-id B-pilot-primary --smoke

# Read existing batch summary (no run). If the smoke has not been launched, this
# fails fast with a clear message and exit code 1.
paper2-pilot-smoke-status:
	@if [ -f paper2/results/B-pilot-primary/batch_summary.json ]; then \
	    cat paper2/results/B-pilot-primary/batch_summary.json; \
	else \
	    echo "no batch_summary.json at paper2/results/B-pilot-primary/ — has the smoke run yet?"; \
	    exit 1; \
	fi

# --- Step 7: full-profile pilot batches (require --allow-step7-batch) ---
paper2-pilot-B-pilot-primary-full:
	$(PYTHON) scripts/paper2_run_pilot_batch.py --batch-id B-pilot-primary --full --allow-step7-batch --force

paper2-pilot-B-pilot-capacity:
	$(PYTHON) scripts/paper2_run_pilot_batch.py --batch-id B-pilot-capacity --full --allow-step7-batch

paper2-pilot-B-pilot-blackout:
	$(PYTHON) scripts/paper2_run_pilot_batch.py --batch-id B-pilot-blackout --full --allow-step7-batch

paper2-pilot-B-pilot-ablation:
	$(PYTHON) scripts/paper2_run_pilot_batch.py --batch-id B-pilot-ablation --full --allow-step7-batch

paper2-pilot-full: paper2-pilot-B-pilot-primary-full paper2-pilot-B-pilot-capacity \
                   paper2-pilot-B-pilot-blackout paper2-pilot-B-pilot-ablation

paper2-pilot-gate:
	$(PYTHON) scripts/paper2_compute_pilot_gate.py

# --- Step 8: primary batches at n=30 (require --allow-step8-batch) ---
paper2-primary-B-primary-primary:
	$(PYTHON) scripts/paper2_run_primary_batch.py --batch-id B-primary-primary --allow-step8-batch

paper2-primary-B-primary-capacity:
	$(PYTHON) scripts/paper2_run_primary_batch.py --batch-id B-primary-capacity --allow-step8-batch

paper2-primary-B-primary-blackout:
	$(PYTHON) scripts/paper2_run_primary_batch.py --batch-id B-primary-blackout --allow-step8-batch

paper2-primary-B-primary-ablation:
	$(PYTHON) scripts/paper2_run_primary_batch.py --batch-id B-primary-ablation --allow-step8-batch

paper2-primary-full: paper2-primary-B-primary-primary paper2-primary-B-primary-capacity \
                    paper2-primary-B-primary-blackout paper2-primary-B-primary-ablation

paper2-primary-status:
	@for b in B-primary-primary B-primary-capacity B-primary-blackout B-primary-ablation; do \
	    if [ -f "paper2/results/$$b/batch_summary.json" ]; then \
	        echo "--- $$b ---"; cat paper2/results/$$b/batch_summary.json; \
	    else \
	        echo "MISSING $$b"; \
	    fi; \
	done

paper2-primary-complete:
	$(PYTHON) scripts/paper2_compute_primary_completion.py

# --- Step 9: aggregation + inference + figures + audit (no manuscript prose) ---
paper2-step9:
	$(PYTHON) scripts/paper2_generate_step9_outputs.py

# Multi-t0 feasibility: aggregate UNIQUE distinct positive CVEs across monthly t0
# windows over the EPSS v3 era. Needs NVD_API_KEY (full multi-year disclosure
# universe is fetched in paced <=120-day chunks; resumable via --resume).
paper2-multit0-probe:
	$(PYTHON) scripts/paper2_feasibility_probe.py \
	  --multi-t0 \
	  --t0-start 2023-09-01 \
	  --t0-end 2025-02-01 \
	  --t0-frequency monthly \
	  --nvd-lookback-days 730 \
	  --h-days 30 \
	  --fleet-size 500 \
	  --seed 20260601 \
	  --nvd-sleep-seconds 6 \
	  --out paper2/feasibility/probe_v2_multit0 \
	  --min-positive-cves 50

clean:
	rm -rf build dist .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
