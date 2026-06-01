# Paper 2 feasibility probe summary

**Feasibility probe only; not a calibrated result, not a paper claim.**

- params: {"start_date": "2024-05-04", "end_date": "2024-08-31", "t0": "2024-09-01", "h_days": 30, "horizon_end": "2024-10-01", "label_window_end": "2024-10-01", "fleet_size": 500, "seed": 20260601, "min_positive_cves": 50, "include_poc": false, "use_cached_only": false, "skip_fetch": false}

## Counts

- total_nvd_records: 13050
- normalized_cves: 12635
- cves_with_cpe: 10337
- catalog_matched_cves: 281
- cves_for_pairs_disclosed_le_t0: 281
- hosts_generated: 500
- pairs_built: 54717
- distinct_cves_in_pairs: 281
- label_a_positive_cves: 0
- label_a_negative_cves: 281
- positive_pairs: 0
- negative_pairs: 54717
- kev_asof_t0_count: 1159
- kev_future_label_count: 0
- epss_t0_rows: 258100

## Calibration

- {"attempted": false, "reason": "positive distinct CVEs 0 < min 50"}

## Probe decision: **PIVOT_away_from_calibration**

