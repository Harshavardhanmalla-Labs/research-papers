# stop_rule_summary

- rows: 12
- columns: ['batch_id', 'rule_id', 'measured', 'threshold', 'reason']

          batch_id rule_id  measured  threshold                                        reason
 B-primary-primary      K1         7         20                      calibration_pivot_locked
 B-primary-primary     S-A         7         20 mirrors K1; calibration experiments forbidden
 B-primary-primary      K3         7         20       unique_positive < threshold (OR branch)
B-primary-capacity      K1         7         20                      calibration_pivot_locked
B-primary-capacity     S-A         7         20 mirrors K1; calibration experiments forbidden
B-primary-capacity      K3         7         20       unique_positive < threshold (OR branch)
B-primary-blackout      K1         7         20                      calibration_pivot_locked
B-primary-blackout     S-A         7         20 mirrors K1; calibration experiments forbidden
B-primary-blackout      K3         7         20       unique_positive < threshold (OR branch)
B-primary-ablation      K1         7         20                      calibration_pivot_locked
B-primary-ablation     S-A         7         20 mirrors K1; calibration experiments forbidden
B-primary-ablation      K3         7         20       unique_positive < threshold (OR branch)
