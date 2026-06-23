#!/usr/bin/env python3
"""Statistical-analysis smoke on a tiny deterministic toy frame.

No experiment run, no fake paper results. This demonstrates the Phase 10
statistical helper APIs (paired means, mean difference, Cohen's d,
Wilcoxon signed-rank, bootstrap CI, Holm-Bonferroni adjustment, and the
minimum detectable effect) on a *synthetic* per-seed metric frame.

The metric is ``ehd_absolute`` (expected exploited-host-days; lower is
better). The toy values are arranged so that
    oracle < proposed_full < epss_only < random
for every seed. This is a fixed arithmetic construction -- NOT a measured
result -- so the printed p-values and effect sizes are properties of the
synthetic numbers, not evidence about any real strategy.
"""

from __future__ import annotations

import pandas as pd

from paper1.evaluation.statistical_tests import (
    bootstrap_ci,
    compare_to_baseline,
    holm_bonferroni,
    minimum_detectable_effect,
    paired_arrays,
    paired_cohens_d,
    paired_mean_difference,
    wilcoxon_signed_rank,
)

N_SEEDS = 30
METRIC = "ehd_absolute"
# Per-seed base levels plus a small strategy-dependent deterministic jitter so
# that paired differences vary across seeds (finite Cohen's d, non-degenerate
# bootstrap CI) while the ordering oracle < proposed_full < epss_only < random
# holds for every seed (jitter range << the smallest base-level gap of 15).
LEVELS = {"random": 100.0, "epss_only": 70.0, "proposed_full": 50.0, "oracle": 35.0}
_STRAT_PHASE = {"random": 0, "epss_only": 2, "proposed_full": 4, "oracle": 1}


def _toy_frame() -> pd.DataFrame:
    rows: list[dict] = []
    for s in range(1, N_SEEDS + 1):
        for strat, base in LEVELS.items():
            # Deterministic, hash-free jitter in [0, ~4) varying by (seed, strat).
            jitter = ((s + _STRAT_PHASE[strat]) % 9) * 0.5
            rows.append(
                {"seed": s, "strategy": strat, "metric": METRIC, "value": base + jitter}
            )
    return pd.DataFrame(rows)


def main() -> int:
    df = _toy_frame()
    baseline = "random"
    candidates = ["epss_only", "proposed_full", "oracle"]

    print(f"=== toy per-seed metric frame ({N_SEEDS} seeds, metric={METRIC!r}) ===")
    print("paired means (lower = fewer exploited-host-days):")
    for strat in [baseline, *candidates]:
        col = df[(df["strategy"] == strat) & (df["metric"] == METRIC)]["value"]
        print(f"  {strat:14s} mean={col.mean():.3f}")

    print(f"\n=== paired comparisons vs baseline {baseline!r} ===")
    p_map: dict[str, float] = {}
    for strat in candidates:
        base, cand, seeds = paired_arrays(df, METRIC, baseline, strat)
        mdiff = paired_mean_difference(cand, base)
        d = paired_cohens_d(cand, base)
        w_stat, p = wilcoxon_signed_rank(cand, base)
        res = compare_to_baseline(df, METRIC, baseline, strat, seed=0)
        p_map[res.comparison_name] = p
        print(
            f"  {strat:14s} n={len(seeds):2d} mean_diff={mdiff:+8.3f} "
            f"cohens_d={d:+8.3f} W={w_stat:7.1f} p={p:.3e} "
            f"bootstrap_CI=[{res.ci_low:+.3f}, {res.ci_high:+.3f}]"
        )

    print("\n=== Holm-Bonferroni family-wise adjustment ===")
    holm = holm_bonferroni(p_map, alpha=0.05)
    for name, info in holm.items():
        print(
            f"  {name:32s} p={info['p_value']:.3e} "
            f"p_adj={info['p_value_adjusted']:.3e} reject_null={info['reject_null']}"
        )

    print("\n=== single-sample bootstrap CI (proposed_full absolute) ===")
    pf = df[(df["strategy"] == "proposed_full") & (df["metric"] == METRIC)]["value"].to_numpy()
    lo, hi = bootstrap_ci(pf, seed=0)
    print(f"  mean={pf.mean():.3f}  95% percentile CI=[{lo:.3f}, {hi:.3f}]")

    print("\n=== minimum detectable effect (paired, power=0.80, alpha=0.05) ===")
    mde = minimum_detectable_effect(N_SEEDS)
    print(f"  n={N_SEEDS}: standardized MDE (Cohen's d) ~= {mde:.3f}")

    print(
        "\nNOTE: values above are arithmetic properties of a synthetic toy "
        "frame, NOT measured experimental results."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
