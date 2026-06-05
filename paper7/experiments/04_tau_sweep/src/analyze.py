"""Analyse Paper 11 tau sweep: H1-H4 outcomes + LaTeX tables."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "primary_v1"
TABLES = ROOT / "submission" / "ieee" / "tables"
TABLES.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df = pd.read_csv(RESULTS / "tau_sweep_results.csv")
    cp = pd.read_csv(RESULTS / "changepoint_log.csv")
    print(f"Loaded {len(df)} P@50 rows, {len(cp)} cp rows.")

    means = df.groupby(["tau", "cell_K", "window", "strategy"])["p_at_50"].mean().unstack("strategy").reset_index()
    means["d_ad_fix"] = means["adaptive"] - means["fixed"]
    means["d_ad_lag1"] = means["adaptive"] - means["lag1"]
    means.to_csv(RESULTS / "cell_window_means.csv", index=False)

    taus = sorted(means.tau.unique())
    Ks = sorted(means.cell_K.unique())

    # Per-tau aggregates
    per_tau = []
    for tau in taus:
        sub = means[means.tau == tau]
        worst_k200 = float(sub[(sub.cell_K == 200) & (sub.window >= 2)]["d_ad_fix"].min())
        cell_k50 = float(sub[(sub.cell_K == 50) & (sub.window >= 2)]["d_ad_lag1"].mean())
        cell_k100 = float(sub[(sub.cell_K == 100) & (sub.window >= 2)]["d_ad_lag1"].mean())
        cell_k200_adfix = float(sub[(sub.cell_K == 200) & (sub.window >= 2)]["d_ad_fix"].mean())
        fire_overall = float(cp[cp.tau == tau].cp_fired.mean())
        fire_per_K = {int(K): float(cp[(cp.tau == tau) & (cp.cell_K == K) & (cp.window >= 2)].cp_fired.mean())
                       for K in Ks}
        per_tau.append({
            "tau": tau,
            "worst_K200_dadfix": worst_k200,
            "cellmean_K50_dadlag1": cell_k50,
            "cellmean_K100_dadlag1": cell_k100,
            "cellmean_K200_dadfix": cell_k200_adfix,
            "fire_overall": fire_overall,
            "fire_K50": fire_per_K.get(50, np.nan),
            "fire_K100": fire_per_K.get(100, np.nan),
            "fire_K200": fire_per_K.get(200, np.nan),
        })
    pt = pd.DataFrame(per_tau)
    pt.to_csv(RESULTS / "per_tau_summary.csv", index=False)

    # H1: Spearman(tau, worst_K200_dadfix) >= +0.8
    rho_h1, p_h1 = spearmanr(pt.tau, pt.worst_K200_dadfix)
    H1 = bool(rho_h1 >= 0.8)

    # H2: Spearman(tau, cellmean_K50_dadlag1) <= -0.8
    rho_h2, p_h2 = spearmanr(pt.tau, pt.cellmean_K50_dadlag1)
    H2 = bool(rho_h2 <= -0.8)

    # H3: any tau passes both:
    #   worst_K200_dadfix >= -0.01 AND cellmean_K50_dadlag1 >= -0.02
    h3_candidates = pt[(pt.worst_K200_dadfix >= -0.01) & (pt.cellmean_K50_dadlag1 >= -0.02)]
    H3 = bool(len(h3_candidates) > 0)
    h3_taus = h3_candidates.tau.tolist()

    # H4: Spearman(tau, fire_overall) >= +0.8
    rho_h4, p_h4 = spearmanr(pt.tau, pt.fire_overall)
    H4 = bool(rho_h4 >= 0.8)

    summary = {
        "n_rows": int(len(df)),
        "per_tau": pt.round(4).to_dict("records"),
        "H1_worst_K200_monotone_in_tau": {"supported": H1, "rho": float(rho_h1), "p": float(p_h1)},
        "H2_K50_cost_monotone_in_tau": {"supported": H2, "rho": float(rho_h2), "p": float(p_h2)},
        "H3_operating_point_exists": {"supported": H3, "qualifying_taus": h3_taus},
        "H4_fire_monotone_in_tau": {"supported": H4, "rho": float(rho_h4), "p": float(p_h4)},
    }
    with open(RESULTS / "hypothesis_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)

    # tab_per_tau: aggregate per tau
    lines = [
        "\\begin{table*}[!t]",
        "  \\caption{Per-$\\tau$ aggregates over the sweep. ``Worst $\\Delta^{\\mathrm{ad-fix}}_{K=200}$'' is the minimum per-window adaptive--fixed cell-mean at K=200; H3 requires it $\\geq -0.01$. ``Cell-mean $\\Delta^{\\mathrm{ad-lag1}}_{K=50}$'' is the K=50 H2 cost; H3 requires it $\\geq -0.02$.}",
        "  \\label{tab:per_tau}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{6pt}",
        "  \\begin{tabular}{c cc cccc c}",
        "    \\toprule",
        "    $\\tau$ & worst $\\Delta^{\\mathrm{ad-fix}}_{K=200}$ & mean $\\Delta^{\\mathrm{ad-fix}}_{K=200}$ & $\\Delta^{\\mathrm{ad-lag1}}_{K=50}$ & $\\Delta^{\\mathrm{ad-lag1}}_{K=100}$ & fire K50 & fire K100 & fire K200 \\\\",
        "    \\midrule",
    ]
    for _, r in pt.iterrows():
        lines.append(
            f"    {r['tau']:.3f} & {r['worst_K200_dadfix']:+.3f} & {r['cellmean_K200_dadfix']:+.3f} & "
            f"{r['cellmean_K50_dadlag1']:+.3f} & {r['cellmean_K100_dadlag1']:+.3f} & "
            f"{r['fire_K50']*100:.0f}\\% & {r['fire_K100']*100:.0f}\\% & {r['fire_K200']*100:.0f}\\% \\\\"
        )
    lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table*}"]
    (TABLES / "tab_per_tau.tex").write_text("\n".join(lines) + "\n")

    # tab_hypotheses
    lines = [
        "\\begin{table}[!t]",
        "  \\caption{Pre-registered hypothesis outcomes.}",
        "  \\label{tab:hypotheses}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{4pt}",
        "  \\begin{tabular}{@{}p{0.5cm}p{4.7cm}p{2.1cm}@{}}",
        "    \\toprule",
        "    \\textbf{ID} & \\textbf{Decision rule} & \\textbf{Outcome} \\\\",
        "    \\midrule",
        f"    H1 & Spearman$(\\tau, \\mathrm{{worst}}\\,\\Delta^{{\\mathrm{{ad-fix}}}}_{{K=200}})\\geq +0.8$ & "
        + ("Supported" if H1 else f"Rejected ($\\rho={rho_h1:.2f}$)") + " \\\\",
        f"    H2 & Spearman$(\\tau, \\Delta^{{\\mathrm{{ad-lag1}}}}_{{K=50}})\\leq -0.8$ & "
        + ("Supported" if H2 else f"Rejected ($\\rho={rho_h2:.2f}$)") + " \\\\",
        f"    H3 & $\\exists\\,\\tau$: worst $K=200\\geq -0.01$ \\& $K=50\\geq -0.02$ & "
        + ("Supported" if H3 else "Rejected") + " \\\\",
        f"    H4 & Spearman$(\\tau, \\mathrm{{fire\\,frac}})\\geq +0.8$ & "
        + ("Supported" if H4 else f"Rejected ($\\rho={rho_h4:.2f}$)") + " \\\\",
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    (TABLES / "tab_hypotheses.tex").write_text("\n".join(lines) + "\n")

    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
