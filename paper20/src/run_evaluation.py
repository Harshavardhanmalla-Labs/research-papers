#!/usr/bin/env python3
"""
Paper 20 - Context-Aware Ensemble for Vulnerability Prioritization in Critical Infrastructure.
Reproducible, pre-registered synthetic evaluation. All parameters are fixed below and frozen
before inspection of results. Run: python3 run_evaluation.py  (writes results/primary_v1/).

Design (honest synthetic): each evaluation cycle produces a pool of vulnerability-instance
"tickets" that must be triaged across a ~50,000-endpoint government fleet. Each ticket carries
the features the paper lists (Static Vulnerability, Threat Intelligence, Environmental Context).
A latent operational-urgency process determines the ground-truth high-risk label as a function
of exploitability AND environmental context AND severity, plus noise - so a CVSS-only ranker,
which sees severity alone, is information-limited by construction, while the full-feature
ensemble can recover urgency. We report whatever the metrics actually are.
"""
import json, os, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

# ------------------------- PRE-REGISTERED PARAMETERS (frozen) -------------------------
SEEDS            = list(range(500, 525))     # 25 evaluation seeds
N_CYCLES         = 18                         # 18 monthly Patch-Tuesday cycles (18 months)
ITEMS_PER_CYCLE  = 600                        # triage tickets per cycle
TRAIN_CYCLES     = 12                         # first 12 cycles train, last 6 evaluate
FLEET_SIZE       = 50_000                     # endpoints (context generator scale)
TOP_K            = 50                         # Precision@K headline
TIER_FRAC        = 0.20                       # "highest priority tier" = top 20%
CAPACITY_PER_DAY = 40                         # remediation capacity (tickets/day) per cycle
SLA_WINDOW_DAYS  = 7                          # compliance window for high-risk tickets
# latent urgency weights (exploit, context, severity) - fixed design priors, not tuned to a target
W_EXPLOIT, W_CONTEXT, W_SEVERITY = 1.30, 1.05, 0.65
URGENCY_NOISE    = 0.20                       # label noise (std of latent noise)
BASE_RATE_TARGET = 0.12                       # ~12% of tickets are truly high-risk (threshold set per cycle)
N_BOOT           = 10_000                     # BCa bootstrap resamples
OUT_DIR          = os.path.join(os.path.dirname(__file__), "..", "results", "primary_v1")

CVSS_AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}
CVSS_AC = {"L": 0.77, "H": 0.44}
CVSS_PR = {"N": 0.85, "L": 0.62, "H": 0.27}
CVSS_UI = {"N": 0.85, "R": 0.62}
CVSS_CIA = {"N": 0.0, "L": 0.22, "H": 0.56}

def cvss_base(av, ac, pr, ui, c, i, a):
    iss = 1 - (1 - CVSS_CIA[c]) * (1 - CVSS_CIA[i]) * (1 - CVSS_CIA[a])
    impact = 6.42 * iss
    expl = 8.22 * CVSS_AV[av] * CVSS_AC[ac] * CVSS_PR[pr] * CVSS_UI[ui]
    if impact <= 0:
        return 0.0
    base = min(impact + expl, 10.0)
    return round(np.ceil(base * 10) / 10, 1)

def gen_cycle(rng):
    n = ITEMS_PER_CYCLE
    av = rng.choice(list(CVSS_AV), n, p=[0.55, 0.15, 0.25, 0.05])
    ac = rng.choice(list(CVSS_AC), n, p=[0.80, 0.20])
    pr = rng.choice(list(CVSS_PR), n, p=[0.45, 0.40, 0.15])
    ui = rng.choice(list(CVSS_UI), n, p=[0.60, 0.40])
    cc = rng.choice(list(CVSS_CIA), n, p=[0.20, 0.30, 0.50])
    ii = rng.choice(list(CVSS_CIA), n, p=[0.20, 0.30, 0.50])
    aa = rng.choice(list(CVSS_CIA), n, p=[0.25, 0.30, 0.45])
    base = np.array([cvss_base(*t) for t in zip(av, ac, pr, ui, cc, ii, aa)])

    # exploit latent -> epss-like prob, KEV, PoC, ATT&CK count
    z_expl = rng.normal(0, 1, n) + 0.4 * (base / 10 - 0.5)
    epss = 1 / (1 + np.exp(-(z_expl - 0.3)))                 # exploit-likelihood score in [0,1]
    poc  = (rng.uniform(size=n) < np.clip(0.10 + 0.55 * epss, 0, 0.95)).astype(int)
    kev  = (rng.uniform(size=n) < np.clip(0.02 + 0.45 * epss * poc, 0, 0.9)).astype(int)
    attck = rng.poisson(0.6 + 1.8 * epss).clip(0, 6)

    # environmental context
    crit = rng.choice([0.15, 0.4, 0.7, 1.0], n, p=[0.45, 0.30, 0.18, 0.07])   # asset criticality
    exposure = np.clip(rng.beta(1.6, 4.0, n), 0, 1)                            # internet exposure
    patch_age = rng.gamma(2.0, 9.0, n).clip(0, 120)                            # days unpatched
    vuln_density = rng.poisson(3.0 + 8.0 * exposure).clip(0, 40)               # vulns per affected asset

    # latent operational urgency (ground truth)
    exploit_sig = 0.55 * epss + 0.25 * kev + 0.12 * poc + 0.08 * (attck / 6)
    context_sig = 0.45 * crit + 0.30 * exposure + 0.15 * (patch_age / 120) + 0.10 * (vuln_density / 40)
    severity_sig = base / 10
    urgency = (W_EXPLOIT * exploit_sig + W_CONTEXT * context_sig +
               W_SEVERITY * severity_sig + rng.normal(0, URGENCY_NOISE, n))
    thr = np.quantile(urgency, 1 - BASE_RATE_TARGET)
    high_risk = (urgency >= thr).astype(int)

    return pd.DataFrame(dict(
        cvss_base=base, av=av, ac=ac, pr=pr, ui=ui, c=cc, i=ii, a=aa,
        epss=epss, kev=kev, poc=poc, attck=attck,
        asset_criticality=crit, exposure=exposure, patch_age=patch_age, vuln_density=vuln_density,
        high_risk=high_risk,
    ))

FEATURES = ["cvss_base", "epss", "kev", "poc", "attck",
            "asset_criticality", "exposure", "patch_age", "vuln_density"]
ONEHOT = ["av", "ac", "pr", "ui", "c", "i", "a"]

def encode(df):
    X = df[FEATURES].copy()
    for col in ONEHOT:
        d = pd.get_dummies(df[col], prefix=col)
        X = pd.concat([X, d], axis=1)
    return X

def scheduler_metrics(order_idx, high, n):
    """Remediate tickets in `order_idx` priority order at CAPACITY_PER_DAY/day.
    Returns (mttr_days over high-risk, sla_rate within window)."""
    day_remediated = np.empty(n)
    for rank, idx in enumerate(order_idx):
        day_remediated[idx] = (rank // CAPACITY_PER_DAY) + 1
    hr = high == 1
    mttr = float(day_remediated[hr].mean()) if hr.any() else 0.0
    sla = float((day_remediated[hr] <= SLA_WINDOW_DAYS).mean()) if hr.any() else 0.0
    return mttr, sla

def eval_scores(scores, df):
    """Given a per-ticket priority score (higher = more urgent), evaluate within each test cycle."""
    rows = []
    for cyc, sub in df.groupby("cycle"):
        s = scores[sub.index.values]
        high = sub["high_risk"].values
        n = len(sub)
        order = np.argsort(-s)                      # descending priority
        topk = order[:TOP_K]
        prec_at_k = high[topk].mean()
        tier_n = max(1, int(round(TIER_FRAC * n)))
        tier = set(order[:tier_n].tolist())
        in_tier = np.array([j in tier for j in range(n)])
        miss_rate = ((high == 1) & (~in_tier)).sum() / max(1, (high == 1).sum())
        fpr = ((high == 0) & (in_tier)).sum() / max(1, (high == 0).sum())
        # scheduler needs a full ordering across the cycle's tickets
        order_local = order
        mttr, sla = scheduler_metrics(order_local, high, n)
        rows.append((prec_at_k, miss_rate, fpr, mttr, sla))
    arr = np.array(rows)
    return dict(precision_at_50=arr[:, 0].mean(), miss_rate=arr[:, 1].mean(),
                fpr=arr[:, 2].mean(), mttr_days=arr[:, 3].mean(), sla_rate=arr[:, 4].mean())

def run_seed(seed):
    rng = np.random.default_rng(seed)
    cycles = []
    for c in range(N_CYCLES):
        d = gen_cycle(rng); d["cycle"] = c; cycles.append(d)
    df = pd.concat(cycles, ignore_index=True)
    train = df[df.cycle < TRAIN_CYCLES]
    test = df[df.cycle >= TRAIN_CYCLES].reset_index(drop=True)
    Xtr, ytr = encode(train), train["high_risk"].values
    Xte = encode(test).reindex(columns=Xtr.columns, fill_value=0)

    rf = RandomForestClassifier(n_estimators=300, max_depth=None, min_samples_leaf=3,
                                random_state=seed, n_jobs=4).fit(Xtr, ytr)
    xgb = XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.08, subsample=0.9,
                        colsample_bytree=0.9, random_state=seed, n_jobs=4,
                        eval_metric="logloss").fit(Xtr, ytr)
    p_rf = rf.predict_proba(Xte)[:, 1]
    p_xgb = xgb.predict_proba(Xte)[:, 1]
    p_ens = (p_rf + p_xgb) / 2

    out = []
    methods = {
        "proposed_ensemble": p_ens,
        "rf_only": p_rf,
        "xgb_only": p_xgb,
        "cvss_only": test["cvss_base"].values,
        "epss_only": test["epss"].values,
        "random": rng.uniform(size=len(test)),
    }
    for name, sc in methods.items():
        m = eval_scores(np.asarray(sc, dtype=float), test)
        m.update(seed=seed, method=name)
        out.append(m)
    return out

def bca_ci(deltas, n_boot=N_BOOT, seed=12345):
    from scipy.stats import norm
    deltas = np.asarray(deltas, float); n = len(deltas); rng = np.random.default_rng(seed)
    boot = np.array([rng.choice(deltas, n, replace=True).mean() for _ in range(n_boot)])
    th = deltas.mean()
    z0 = norm.ppf((boot < th).mean()) if 0 < (boot < th).mean() < 1 else 0.0
    jk = np.array([np.delete(deltas, i).mean() for i in range(n)])
    jbar = jk.mean(); num = ((jbar - jk) ** 3).sum(); den = 6 * (((jbar - jk) ** 2).sum() ** 1.5)
    acc = num / den if den != 0 else 0.0
    def adj(al):
        z = norm.ppf(al); p = norm.cdf(z0 + (z0 + z) / (1 - acc * (z0 + z))); return np.quantile(boot, p)
    return float(th), float(adj(0.025)), float(adj(0.975))

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    for s in SEEDS:
        rows.extend(run_seed(s))
        print(f"seed {s} done")
    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(OUT_DIR, "primary_results.csv"), index=False)

    metrics = ["precision_at_50", "miss_rate", "fpr", "mttr_days", "sla_rate"]
    summary = {}
    piv = res.pivot_table(index="seed", columns="method", values=metrics)
    means = res.groupby("method")[metrics].mean()
    means.to_csv(os.path.join(OUT_DIR, "metrics_by_method.csv"))

    # Pre-registered hypotheses: proposed_ensemble vs cvss_only baseline, paired by seed (BCa CI).
    hyp = {}
    base = "cvss_only"
    for m, better_is_lower in [("precision_at_50", False), ("miss_rate", True),
                               ("fpr", True), ("mttr_days", True), ("sla_rate", False)]:
        a = piv[m]["proposed_ensemble"].values
        b = piv[m][base].values
        d = (a - b)
        mean, lo, hi = bca_ci(d)
        # "supported" = CI excludes zero in the improvement direction
        if better_is_lower:
            supported = hi < 0
        else:
            supported = lo > 0
        hyp[m] = dict(proposed=float(a.mean()), cvss_only=float(b.mean()),
                      delta_mean=mean, ci_low=lo, ci_high=hi, supported=bool(supported))
    summary["n_seeds"] = len(SEEDS)
    summary["params"] = dict(N_CYCLES=N_CYCLES, ITEMS_PER_CYCLE=ITEMS_PER_CYCLE,
                             TRAIN_CYCLES=TRAIN_CYCLES, TOP_K=TOP_K, TIER_FRAC=TIER_FRAC,
                             CAPACITY_PER_DAY=CAPACITY_PER_DAY, SLA_WINDOW_DAYS=SLA_WINDOW_DAYS,
                             base_rate_target=BASE_RATE_TARGET,
                             urgency_weights=[W_EXPLOIT, W_CONTEXT, W_SEVERITY],
                             urgency_noise=URGENCY_NOISE, seeds=[SEEDS[0], SEEDS[-1]])
    summary["headline"] = {m: round(float(means.loc["proposed_ensemble", m]), 4) for m in metrics}
    summary["baseline_cvss_only"] = {m: round(float(means.loc[base, m]), 4) for m in metrics}
    summary["hypotheses"] = hyp
    json.dump(summary, open(os.path.join(OUT_DIR, "hypothesis_summary.json"), "w"), indent=2)
    print("\n=== HEADLINE (proposed ensemble, mean over seeds) ===")
    for m in metrics:
        print(f"  {m:16} ensemble={means.loc['proposed_ensemble', m]:.4f}  cvss_only={means.loc[base, m]:.4f}")
    print("frozen ->", OUT_DIR)

if __name__ == "__main__":
    main()
