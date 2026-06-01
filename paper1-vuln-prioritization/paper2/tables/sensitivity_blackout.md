# sensitivity_blackout

- rows: 9
- columns: ['cell_id', 'strategy', 'weight_vector', 'capacity_ratio', 'blackout_policy', 'approver_policy', 'ablation', 'n_seeds', 'ehd_mean', 'ehd_median', 'ehd_std', 'axis']

                                 cell_id             strategy        weight_vector  capacity_ratio blackout_policy approver_policy ablation  n_seeds     ehd_mean   ehd_median      ehd_std     axis
                     BLK-epss_only-light            epss_only                   na            0.01           light               A     full       30 3.320629e+09 3303966096.0 8.020796e+07 blackout
                      BLK-epss_only-none            epss_only                   na            0.01            none               A     full       30 3.318396e+09 3301745184.0 8.015405e+07 blackout
                    BLK-epss_only-strict            epss_only                   na            0.01          strict               A     full       30 3.326209e+09 3309519312.0 8.034259e+07 blackout
   BLK-proposed-w_context_dominant-light proposed_fixed_prior   w_context_dominant            0.01           light               A     full       30 3.303104e+09 3285758152.0 8.077172e+07 blackout
    BLK-proposed-w_context_dominant-none proposed_fixed_prior   w_context_dominant            0.01            none               A     full       30 3.299470e+09 3282074280.0 8.076250e+07 blackout
  BLK-proposed-w_context_dominant-strict proposed_fixed_prior   w_context_dominant            0.01          strict               A     full       30 3.312191e+09 3294964736.0 8.079377e+07 blackout
 BLK-proposed-w_paper1_placeholder-light proposed_fixed_prior w_paper1_placeholder            0.01           light               A     full       30 3.311092e+09 3294131632.0 8.046439e+07 blackout
  BLK-proposed-w_paper1_placeholder-none proposed_fixed_prior w_paper1_placeholder            0.01            none               A     full       30 3.308096e+09 3291118472.0 8.043118e+07 blackout
BLK-proposed-w_paper1_placeholder-strict proposed_fixed_prior w_paper1_placeholder            0.01          strict               A     full       30 3.318580e+09 3301662928.0 8.054734e+07 blackout
