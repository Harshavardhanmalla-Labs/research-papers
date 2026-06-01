# Paper 2 multi-t0 feasibility probe summary

**Feasibility probe only; not a calibrated result, not a paper claim.**

- params: {"t0_start": "2023-09-01", "t0_end": "2025-02-01", "t0_frequency": "monthly", "h_days": 30, "nvd_lookback_days": 730, "fleet_size": 500, "seed": 20260601, "min_positive_cves": 50, "use_cached_only": false, "skip_fetch": false, "aggregate_positive_cves": true, "nvd_api_key_present": true}

## Aggregate counts (gating metric: UNIQUE distinct positive CVEs)

- n_windows: 18
- t0_start: 2023-09-01
- t0_end: 2025-02-01
- universe_start: 2021-09-01
- universe_end: 2025-02-01
- nvd_lookback_days: 730
- h_days: 30
- total_nvd_records: 110224
- normalized_cves: 104495
- cves_with_cpe: 95006
- catalog_matched_cves: 2688
- union_distinct_cves_in_pairs: 2688
- unique_positive_cves: 7
- unique_negative_cves: 2681
- event_positive_cves_across_windows: 7

## Per-window positive CVEs

- 2023-09-01: positive_cves_this_window=0, distinct_cves_in_pairs=1673, pairs_built=332915
- 2023-10-01: positive_cves_this_window=2, distinct_cves_in_pairs=1733, pairs_built=344353
- 2023-11-01: positive_cves_this_window=0, distinct_cves_in_pairs=1812, pairs_built=355772
- 2023-12-01: positive_cves_this_window=2, distinct_cves_in_pairs=1860, pairs_built=365621
- 2024-01-01: positive_cves_this_window=1, distinct_cves_in_pairs=1899, pairs_built=372102
- 2024-02-01: positive_cves_this_window=1, distinct_cves_in_pairs=1963, pairs_built=381894
- 2024-03-01: positive_cves_this_window=0, distinct_cves_in_pairs=2015, pairs_built=392217
- 2024-04-01: positive_cves_this_window=0, distinct_cves_in_pairs=2063, pairs_built=400722
- 2024-05-01: positive_cves_this_window=0, distinct_cves_in_pairs=2121, pairs_built=410390
- 2024-06-01: positive_cves_this_window=0, distinct_cves_in_pairs=2183, pairs_built=422980
- 2024-07-01: positive_cves_this_window=0, distinct_cves_in_pairs=2246, pairs_built=435131
- 2024-08-01: positive_cves_this_window=0, distinct_cves_in_pairs=2322, pairs_built=446599
- 2024-09-01: positive_cves_this_window=0, distinct_cves_in_pairs=2408, pairs_built=466493
- 2024-10-01: positive_cves_this_window=0, distinct_cves_in_pairs=2471, pairs_built=478500
- 2024-11-01: positive_cves_this_window=0, distinct_cves_in_pairs=2546, pairs_built=487802
- 2024-12-01: positive_cves_this_window=0, distinct_cves_in_pairs=2598, pairs_built=495871
- 2025-01-01: positive_cves_this_window=0, distinct_cves_in_pairs=2635, pairs_built=502913
- 2025-02-01: positive_cves_this_window=1, distinct_cves_in_pairs=2688, pairs_built=513037

## Calibration

- {"attempted": false, "reason": "unique positive distinct CVEs 7 < min 50"}

## Probe decision: **PIVOT_away_from_calibration**

