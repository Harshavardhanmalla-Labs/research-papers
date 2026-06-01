# sensitivity_weight_family

- rows: 12
- columns: ['cell_id', 'strategy', 'weight_vector', 'capacity_ratio', 'blackout_policy', 'approver_policy', 'ablation', 'n_seeds', 'ehd_mean', 'ehd_median', 'ehd_std', 'axis']

                        cell_id                strategy        weight_vector  capacity_ratio blackout_policy approver_policy ablation  n_seeds     ehd_mean   ehd_median      ehd_std          axis
                 P-cvss_only-na               cvss_only                   na            0.01         primary               A     full       30 3.322861e+09 3306189744.0 8.026168e+07 weight_family
   P-cvss_plus_epss_plus_kev-na cvss_plus_epss_plus_kev                   na            0.01         primary               A     full       30 3.322861e+09 3306188248.0 8.026178e+07 weight_family
               P-cvss_x_epss-na             cvss_x_epss                   na            0.01         primary               A     full       30 3.322861e+09 3306188160.0 8.026156e+07 weight_family
                 P-epss_only-na               epss_only                   na            0.01         primary               A     full       30 3.322861e+09 3306187152.0 8.026184e+07 weight_family
                 P-kev_first-na               kev_first                   na            0.01         primary               A     full       30 3.322861e+09 3306189520.0 8.026155e+07 weight_family
  P-proposed-w_context_dominant    proposed_fixed_prior   w_context_dominant            0.01         primary               A     full       30 3.306748e+09 3289447000.0 8.078061e+07 weight_family
     P-proposed-w_cvss_dominant    proposed_fixed_prior      w_cvss_dominant            0.01         primary               A     full       30 3.314038e+09 3297584632.0 8.042136e+07 weight_family
     P-proposed-w_epss_dominant    proposed_fixed_prior      w_epss_dominant            0.01         primary               A     full       30 3.320653e+09 3304017936.0 8.023032e+07 weight_family
      P-proposed-w_kev_dominant    proposed_fixed_prior       w_kev_dominant            0.01         primary               A     full       30 3.320316e+09 3303649736.0 8.032251e+07 weight_family
P-proposed-w_paper1_placeholder    proposed_fixed_prior w_paper1_placeholder            0.01         primary               A     full       30 3.314121e+09 3297182440.0 8.049801e+07 weight_family
           P-proposed-w_uniform    proposed_fixed_prior            w_uniform            0.01         primary               A     full       30 3.312835e+09 3295913512.0 8.044845e+07 weight_family
                    P-random-na                  random                   na            0.01         primary               A     full       30 3.322854e+09 3306150576.0 8.026290e+07 weight_family
