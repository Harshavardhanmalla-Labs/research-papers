# Paper 2 multi-t0 feasibility probe summary

**Feasibility probe only; not a calibrated result, not a paper claim.**

- params: {"t0_start": "2024-05-31", "t0_end": "2024-08-31", "t0_frequency": "monthly", "h_days": 30, "nvd_lookback_days": 27, "fleet_size": 200, "seed": 20260601, "min_positive_cves": 50, "use_cached_only": true, "skip_fetch": false, "aggregate_positive_cves": true, "nvd_api_key_present": false}

## Aggregate counts (gating metric: UNIQUE distinct positive CVEs)

- n_windows: 4
- t0_start: 2024-05-31
- t0_end: 2024-08-31
- universe_start: 2024-05-04
- universe_end: 2024-08-31
- nvd_lookback_days: 27
- h_days: 30
- total_nvd_records: 13050
- normalized_cves: 12635
- cves_with_cpe: 10337
- catalog_matched_cves: 281
- union_distinct_cves_in_pairs: 281
- unique_positive_cves: 0
- unique_negative_cves: 281
- event_positive_cves_across_windows: 0

## Per-window positive CVEs

- 2024-05-31: positive_cves_this_window=0, distinct_cves_in_pairs=56, pairs_built=4689
- 2024-06-30: positive_cves_this_window=0, distinct_cves_in_pairs=118, pairs_built=9729
- 2024-07-31: positive_cves_this_window=0, distinct_cves_in_pairs=192, pairs_built=14117
- 2024-08-31: positive_cves_this_window=0, distinct_cves_in_pairs=281, pairs_built=22739

## Calibration

- {"attempted": false, "reason": "unique positive distinct CVEs 0 < min 50"}

## Probe decision: **PIVOT_away_from_calibration**

