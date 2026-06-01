# inference_C1_weight_family

- rows: 15
- meaningful threshold: 5000.0 host-days
- alpha: 0.05

family_id                                comparison_id       metric  n_pairs    mean_delta  median_delta  bootstrap_ci_low  bootstrap_ci_high  wilcoxon_p  holm_p  holm_reject inference_status drop_reason interpretation_guardrail
       C1      w_context_dominant__vs__w_cvss_dominant ehd_absolute       30 -7.290090e+06    -7400920.0     -7.523899e+06      -7.074780e+06         NaN     NaN        False          allowed                          descriptive
       C1      w_context_dominant__vs__w_epss_dominant ehd_absolute       30 -1.390507e+07   -13886592.0     -1.418953e+07      -1.365119e+07         NaN     NaN        False          allowed                          descriptive
       C1       w_context_dominant__vs__w_kev_dominant ehd_absolute       30 -1.356866e+07   -13589056.0     -1.382832e+07      -1.334318e+07         NaN     NaN        False          allowed                          descriptive
       C1 w_context_dominant__vs__w_paper1_placeholder ehd_absolute       30 -7.373633e+06    -7313256.0     -7.584191e+06      -7.179315e+06         NaN     NaN        False          allowed                          descriptive
       C1            w_context_dominant__vs__w_uniform ehd_absolute       30 -6.087277e+06    -5926120.0     -6.384480e+06      -5.803709e+06         NaN     NaN        False          allowed                          descriptive
       C1         w_cvss_dominant__vs__w_epss_dominant ehd_absolute       30 -6.614975e+06    -6604016.0     -6.748383e+06      -6.483456e+06         NaN     NaN        False          allowed                          descriptive
       C1          w_cvss_dominant__vs__w_kev_dominant ehd_absolute       30 -6.278566e+06    -6231680.0     -6.405977e+06      -6.166052e+06         NaN     NaN        False          allowed                          descriptive
       C1    w_cvss_dominant__vs__w_paper1_placeholder ehd_absolute       30 -8.354240e+04      -58384.0     -2.826708e+05       1.455600e+05         NaN     NaN        False          allowed                          descriptive
       C1               w_cvss_dominant__vs__w_uniform ehd_absolute       30  1.202813e+06     1205224.0      9.200322e+05       1.479265e+06         NaN     NaN        False          allowed                          descriptive
       C1          w_epss_dominant__vs__w_kev_dominant ehd_absolute       30  3.364096e+05      306488.0      2.853718e+05       3.928826e+05         NaN     NaN        False          allowed                          descriptive
       C1    w_epss_dominant__vs__w_paper1_placeholder ehd_absolute       30  6.531433e+06     6448080.0      6.342459e+06       6.776160e+06         NaN     NaN        False          allowed                          descriptive
       C1               w_epss_dominant__vs__w_uniform ehd_absolute       30  7.817788e+06     7671064.0      7.521213e+06       8.107344e+06         NaN     NaN        False          allowed                          descriptive
       C1     w_kev_dominant__vs__w_paper1_placeholder ehd_absolute       30  6.195023e+06     6212984.0      6.045835e+06       6.384535e+06         NaN     NaN        False          allowed                          descriptive
       C1                w_kev_dominant__vs__w_uniform ehd_absolute       30  7.481379e+06     7481080.0      7.227971e+06       7.722897e+06         NaN     NaN        False          allowed                          descriptive
       C1          w_paper1_placeholder__vs__w_uniform ehd_absolute       30  1.286355e+06     1410952.0      1.131196e+06       1.413362e+06         NaN     NaN        False          allowed                          descriptive
