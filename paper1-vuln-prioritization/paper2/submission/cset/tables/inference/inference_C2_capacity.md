# inference_C2_capacity

- rows: 5
- meaningful threshold: 5000.0 host-days
- alpha: 0.05

family_id                                                              comparison_id       metric  n_pairs    mean_delta  median_delta  bootstrap_ci_low  bootstrap_ci_high  wilcoxon_p  holm_p  holm_reject inference_status drop_reason interpretation_guardrail
       C2                cvss_plus_epss_plus_kev__na__capacity_ratio__0.02__to__0.05 ehd_absolute       30 -7.701647e+07   -76630008.0     -7.775678e+07      -7.644699e+07         NaN     NaN        False          allowed                          descriptive
       C2                              epss_only__na__capacity_ratio__0.02__to__0.05 ehd_absolute       30 -7.701629e+07   -76628592.0     -7.775610e+07      -7.644654e+07         NaN     NaN        False          allowed                          descriptive
       C2   proposed_fixed_prior__w_context_dominant__capacity_ratio__0.02__to__0.05 ehd_absolute       30 -1.221599e+08  -121835176.0     -1.228902e+08      -1.213429e+08         NaN     NaN        False          allowed                          descriptive
       C2      proposed_fixed_prior__w_epss_dominant__capacity_ratio__0.02__to__0.05 ehd_absolute       30 -1.199496e+08  -119728816.0     -1.206994e+08      -1.193717e+08         NaN     NaN        False          allowed                          descriptive
       C2 proposed_fixed_prior__w_paper1_placeholder__capacity_ratio__0.02__to__0.05 ehd_absolute       30 -1.191404e+08  -119052360.0     -1.200231e+08      -1.183316e+08         NaN     NaN        False          allowed                          descriptive
