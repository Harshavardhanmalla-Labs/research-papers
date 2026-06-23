# Primary completion

- status: **PRIMARY_COMPLETE_VALID**
- reason: all 4 primary batches valid; 1440 seed-runs; freeze OK on every batch; no hard-halt rules; all rows carry freeze_witness_id
- timestamp: 2026-05-28T18:40:48.486729+00:00
- primary batches completed: 4 / 4
- total cells completed: 48
- total seed-runs completed: 1440 / 1440
- total wallclock seconds: 2143.21
- measured per-seed-run seconds: 1.4883
- freeze status all batches: OK
- stop rules triggered: ['K1', 'K3', 'S-A']
- hard halt triggered: []
- all rows have freeze_witness_id: True
- no forbidden operations: True
- paper1 freeze verified after: None

## Per-batch

- **B-primary-primary**: {'batch_id': 'B-primary-primary', 'status': 'OK', 'cells_completed': 12, 'seed_runs_completed': 360, 'wallclock_seconds_total': 488.9582462310791, 'per_seed_run_seconds_mean': 1.3582173506418864, 'freeze_status': 'OK', 'freeze_witness_id': '750e144ba9567b5255b27ce40279643bdf7418d53b15edce5d72c515eb022833', 'stop_rules_triggered': ['K1', 'S-A', 'K3'], 'per_row_total': 2160, 'per_row_missing_witness': 0}
- **B-primary-capacity**: {'batch_id': 'B-primary-capacity', 'status': 'OK', 'cells_completed': 15, 'seed_runs_completed': 450, 'wallclock_seconds_total': 604.7741780281067, 'per_seed_run_seconds_mean': 1.3439426178402372, 'freeze_status': 'OK', 'freeze_witness_id': '750e144ba9567b5255b27ce40279643bdf7418d53b15edce5d72c515eb022833', 'stop_rules_triggered': ['K1', 'S-A', 'K3'], 'per_row_total': 2700, 'per_row_missing_witness': 0}
- **B-primary-blackout**: {'batch_id': 'B-primary-blackout', 'status': 'OK', 'cells_completed': 9, 'seed_runs_completed': 270, 'wallclock_seconds_total': 397.0904700756073, 'per_seed_run_seconds_mean': 1.4707054447244714, 'freeze_status': 'OK', 'freeze_witness_id': '750e144ba9567b5255b27ce40279643bdf7418d53b15edce5d72c515eb022833', 'stop_rules_triggered': ['K1', 'S-A', 'K3'], 'per_row_total': 1620, 'per_row_missing_witness': 0}
- **B-primary-ablation**: {'batch_id': 'B-primary-ablation', 'status': 'OK', 'cells_completed': 12, 'seed_runs_completed': 360, 'wallclock_seconds_total': 652.3878312110901, 'per_seed_run_seconds_mean': 1.8121884200308058, 'freeze_status': 'OK', 'freeze_witness_id': '750e144ba9567b5255b27ce40279643bdf7418d53b15edce5d72c515eb022833', 'stop_rules_triggered': ['K1', 'S-A', 'K3'], 'per_row_total': 2160, 'per_row_missing_witness': 0}
