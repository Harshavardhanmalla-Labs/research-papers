# Pilot gate decision

- decision: **PROCEED_TO_PRIMARY_NO_FALLBACK**
- reason: projected primary 0.83h with safety factor <= 18.0h; freeze OK on all batches; no hard-halt rules
- timestamp: 2026-05-28T17:49:53.708807+00:00
- pilot batches completed: 4 / 4
- pilot seed-runs completed: 288 / 288
- pilot wallclock seconds: 459.54
- measured per-seed-run seconds: 1.5956
- projected primary runtime hours: 0.6383
- projected primary runtime with safety factor: 0.8297
- safety factor: 1.3
- stop rules triggered: ['K1', 'K3', 'S-A']
- freeze status all batches: OK
- hard-halt triggered: []

## Per-batch

- **B-pilot-primary**: {'batch_id': 'B-pilot-primary', 'status': 'OK', 'cells_completed': 12, 'seed_runs_completed': 72, 'wallclock_seconds_total': 114.3425920009613, 'per_seed_run_seconds_mean': 1.588091555568907, 'freeze_status': 'OK', 'freeze_witness_id': '750e144ba9567b5255b27ce40279643bdf7418d53b15edce5d72c515eb022833', 'stop_rules_triggered': ['K1', 'S-A', 'K3']}
- **B-pilot-capacity**: {'batch_id': 'B-pilot-capacity', 'status': 'OK', 'cells_completed': 15, 'seed_runs_completed': 90, 'wallclock_seconds_total': 123.55819439888, 'per_seed_run_seconds_mean': 1.3728688266542224, 'freeze_status': 'OK', 'freeze_witness_id': '750e144ba9567b5255b27ce40279643bdf7418d53b15edce5d72c515eb022833', 'stop_rules_triggered': ['K1', 'S-A', 'K3']}
- **B-pilot-blackout**: {'batch_id': 'B-pilot-blackout', 'status': 'OK', 'cells_completed': 9, 'seed_runs_completed': 54, 'wallclock_seconds_total': 87.5177960395813, 'per_seed_run_seconds_mean': 1.620699926658913, 'freeze_status': 'OK', 'freeze_witness_id': '750e144ba9567b5255b27ce40279643bdf7418d53b15edce5d72c515eb022833', 'stop_rules_triggered': ['K1', 'S-A', 'K3']}
- **B-pilot-ablation**: {'batch_id': 'B-pilot-ablation', 'status': 'OK', 'cells_completed': 12, 'seed_runs_completed': 72, 'wallclock_seconds_total': 134.1237530708313, 'per_seed_run_seconds_mean': 1.862829903761546, 'freeze_status': 'OK', 'freeze_witness_id': '750e144ba9567b5255b27ce40279643bdf7418d53b15edce5d72c515eb022833', 'stop_rules_triggered': ['K1', 'S-A', 'K3']}
