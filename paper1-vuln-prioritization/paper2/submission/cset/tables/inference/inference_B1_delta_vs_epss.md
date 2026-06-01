# inference_B1_delta_vs_epss

- rows: 11
- meaningful threshold: 5000.0 host-days
- alpha: 0.05

family_id                                             comparison_id       metric  n_pairs    mean_delta  median_delta  bootstrap_ci_low  bootstrap_ci_high  wilcoxon_p  holm_p  holm_reject inference_status drop_reason interpretation_guardrail
       B1                              cvss_only__na__vs__epss_only ehd_absolute       30 -1.632000e+02        -144.0     -1.917768e+03       1.328685e+03         NaN     NaN        False          allowed                          descriptive
       B1                cvss_plus_epss_plus_kev__na__vs__epss_only ehd_absolute       30  1.029333e+02         192.0     -2.238956e+02       4.314923e+02         NaN     NaN        False          allowed                          descriptive
       B1                            cvss_x_epss__na__vs__epss_only ehd_absolute       30  3.744000e+02         432.0     -3.840000e+02       1.144628e+03         NaN     NaN        False          allowed                          descriptive
       B1                              kev_first__na__vs__epss_only ehd_absolute       30  1.397333e+02         224.0     -3.562076e+02       8.388046e+02         NaN     NaN        False          allowed                          descriptive
       B1   proposed_fixed_prior__w_context_dominant__vs__epss_only ehd_absolute       30 -1.611319e+07   -16079640.0     -1.640664e+07      -1.585990e+07         NaN     NaN        False          allowed                          descriptive
       B1      proposed_fixed_prior__w_cvss_dominant__vs__epss_only ehd_absolute       30 -8.823101e+06    -8759024.0     -8.974791e+06      -8.684531e+06         NaN     NaN        False          allowed                          descriptive
       B1      proposed_fixed_prior__w_epss_dominant__vs__epss_only ehd_absolute       30 -2.208125e+06    -2204272.0     -2.242188e+06      -2.176141e+06         NaN     NaN        False          allowed                          descriptive
       B1       proposed_fixed_prior__w_kev_dominant__vs__epss_only ehd_absolute       30 -2.544535e+06    -2510912.0     -2.603336e+06      -2.491869e+06         NaN     NaN        False          allowed                          descriptive
       B1 proposed_fixed_prior__w_paper1_placeholder__vs__epss_only ehd_absolute       30 -8.739558e+06    -8727952.0     -8.979784e+06      -8.539422e+06         NaN     NaN        False          allowed                          descriptive
       B1            proposed_fixed_prior__w_uniform__vs__epss_only ehd_absolute       30 -1.002591e+07    -9970440.0     -1.031891e+07      -9.728651e+06         NaN     NaN        False          allowed                          descriptive
       B1                                 random__na__vs__epss_only ehd_absolute       30 -6.854400e+03       -8208.0     -1.722758e+04       3.693343e+03         NaN     NaN        False          allowed                          descriptive
