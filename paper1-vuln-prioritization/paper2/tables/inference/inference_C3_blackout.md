# inference_C3_blackout

- rows: 3
- meaningful threshold: 5000.0 host-days
- alpha: 0.05

family_id                                                                comparison_id       metric  n_pairs   mean_delta  median_delta  bootstrap_ci_low  bootstrap_ci_high  wilcoxon_p  holm_p  holm_reject inference_status drop_reason interpretation_guardrail
       C3                              epss_only__na__blackout_policy__none__to__light ehd_absolute       30 2.232528e+06     2220912.0      2.216029e+06       2.253889e+06         NaN     NaN        False          allowed                          descriptive
       C3   proposed_fixed_prior__w_context_dominant__blackout_policy__none__to__light ehd_absolute       30 3.634655e+06     3633832.0      3.616159e+06       3.653773e+06         NaN     NaN        False          allowed                          descriptive
       C3 proposed_fixed_prior__w_paper1_placeholder__blackout_policy__none__to__light ehd_absolute       30 2.995243e+06     2985944.0      2.974492e+06       3.017681e+06         NaN     NaN        False          allowed                          descriptive
