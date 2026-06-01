# delta_vs_epss

- rows: 12
- columns: ['cell_id', 'strategy', 'weight_vector', 'n_pairs', 'delta_ehd_mean', 'delta_ehd_median', 'delta_ehd_std', 'delta_ehd_min', 'delta_ehd_max', 'baseline_ehd_mean', 'baseline_strategy']

                        cell_id                strategy        weight_vector  n_pairs  delta_ehd_mean  delta_ehd_median  delta_ehd_std  delta_ehd_min  delta_ehd_max  baseline_ehd_mean baseline_strategy
                 P-cvss_only-na               cvss_only                   na       30   -1.632000e+02            -144.0    4684.750480       -12096.0        10080.0       3322860768.0         epss_only
   P-cvss_plus_epss_plus_kev-na cvss_plus_epss_plus_kev                   na       30    1.029333e+02             192.0     958.073316        -1616.0         2480.0       3322860768.0         epss_only
               P-cvss_x_epss-na             cvss_x_epss                   na       30    3.744000e+02             432.0    2181.771656        -3168.0         6048.0       3322860768.0         epss_only
                 P-epss_only-na               epss_only                   na       30    0.000000e+00               0.0       0.000000            0.0            0.0       3322860768.0         epss_only
                 P-kev_first-na               kev_first                   na       30    1.397333e+02             224.0    1656.769081        -2944.0         5280.0       3322860768.0         epss_only
  P-proposed-w_context_dominant    proposed_fixed_prior   w_context_dominant       30   -1.611319e+07       -16079640.0  788188.481720    -17465184.0    -14776112.0       3322860768.0         epss_only
     P-proposed-w_cvss_dominant    proposed_fixed_prior      w_cvss_dominant       30   -8.823101e+06        -8759024.0  411668.400515     -9730032.0     -8027952.0       3322860768.0         epss_only
     P-proposed-w_epss_dominant    proposed_fixed_prior      w_epss_dominant       30   -2.208125e+06        -2204272.0   95108.789231     -2416960.0     -2023680.0       3322860768.0         epss_only
      P-proposed-w_kev_dominant    proposed_fixed_prior       w_kev_dominant       30   -2.544535e+06        -2510912.0  163386.837726     -2955328.0     -2293568.0       3322860768.0         epss_only
P-proposed-w_paper1_placeholder    proposed_fixed_prior w_paper1_placeholder       30   -8.739558e+06        -8727952.0  640845.949859    -10371408.0     -7644960.0       3322860768.0         epss_only
           P-proposed-w_uniform    proposed_fixed_prior            w_uniform       30   -1.002591e+07        -9970440.0  866640.893679    -12005680.0     -8304464.0       3322860768.0         epss_only
                    P-random-na                  random                   na       30   -6.854400e+03           -8208.0   31526.364518       -70560.0        43776.0       3322860768.0         epss_only
