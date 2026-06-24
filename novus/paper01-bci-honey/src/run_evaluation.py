#!/usr/bin/env python3
"""BCI-Honey evaluation — early attacker-intent inference on real honeypot sessions.

Frozen per PREREGISTRATION.md. Uses ONLY early-phase (pre-action) features.
Temporal split: train 2019-05..2019-11, test 2019-12..2020-02.

Task A: engagement (binary, intent != bruteforce)  -> PR-AUC, ROC-AUC, P@1%, P@5%, lift
Task B: intent typing (4-class)                     -> macro-F1, balanced acc, per-class F1
Baselines: prior-rate, protocol-only, n_auth-only / majority, protocol-only.
Uncertainty: BCa bootstrap (10,000) over test sessions; hypotheses H1-H4.

Outputs -> results/primary_v1/
"""
import os, json, re, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score, f1_score, balanced_accuracy_score


def fast_ap(y, s):
    """Average precision — vectorized, matches sklearn definition, fast in the bootstrap loop."""
    order = np.argsort(-s, kind="stable")
    y = y[order]
    tp = np.cumsum(y); fp = np.cumsum(1 - y)
    prec = tp / np.maximum(tp + fp, 1)
    pos = y.sum()
    if pos == 0:
        return 0.0
    rec = tp / pos
    rec_prev = np.concatenate([[0.0], rec[:-1]])
    return float(np.sum((rec - rec_prev) * prec))


def fast_macro_f1(yt, yp, labels):
    f1s = []
    for c in labels:
        tp = np.sum((yp == c) & (yt == c)); fp = np.sum((yp == c) & (yt != c)); fn = np.sum((yp != c) & (yt == c))
        d = 2 * tp + fp + fn
        f1s.append(0.0 if d == 0 else 2.0 * tp / d)
    return float(np.mean(f1s))

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "results", "primary_v1"); os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(20200229)
N_BOOT = 10_000
TRAIN_MONTHS = {"2019-05", "2019-06", "2019-07", "2019-08", "2019-09", "2019-10", "2019-11"}
TEST_MONTHS  = {"2019-12", "2020-01", "2020-02"}

EARLY = ["n_enc", "n_kex", "n_mac", "n_key", "has_hassh", "n_auth", "n_auth_ok",
         "n_distinct_creds", "max_pw_len", "empty_pw", "common_user", "hour"]  # + proto, ssh_ver onehot
LEAKY = {"time_to_action", "n_early_events", "n_cmd", "n_cmd_fail", "n_tcpip",
         "tunnel_port", "n_download", "duration"}
INTENTS = ["bruteforce", "tunneling", "execution", "malware_delivery"]


def clean_ver(s):
    s = str(s)
    m = re.match(r"^b?'?(.*?)'?$", s)
    return (m.group(1) if m else s)[:40] or "none"


def build_features(df, top_vers):
    X = df[EARLY].copy().fillna(0)
    X["proto_telnet"] = (df["proto"] == "telnet").astype(int)
    v = df["ssh_ver"].map(clean_ver)
    for tv in top_vers:
        X[f"ver_{tv}"] = (v == tv).astype(int)
    X["ver_other"] = (~v.isin(top_vers)).astype(int)
    return X


def bca_ci(boot, theta_hat, jack, alpha=0.05):
    boot = np.asarray(boot); jack = np.asarray(jack)
    z0 = _norm_ppf(np.mean(boot < theta_hat))
    jbar = jack.mean()
    num = np.sum((jbar - jack) ** 3); den = 6.0 * (np.sum((jbar - jack) ** 2) ** 1.5) + 1e-12
    a = num / den
    lo = _norm_cdf(z0 + (z0 + _norm_ppf(alpha / 2)) / (1 - a * (z0 + _norm_ppf(alpha / 2))))
    hi = _norm_cdf(z0 + (z0 + _norm_ppf(1 - alpha / 2)) / (1 - a * (z0 + _norm_ppf(1 - alpha / 2))))
    return float(np.quantile(boot, np.clip(lo, 0, 1))), float(np.quantile(boot, np.clip(hi, 0, 1)))


def _norm_cdf(x): from math import erf; return 0.5 * (1 + erf(x / np.sqrt(2)))
def _norm_ppf(p):
    p = min(max(p, 1e-9), 1 - 1e-9)
    # Acklam approximation
    a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00]
    b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,6.680131188771972e+01,-1.328068155288572e+01]
    c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,-2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00]
    d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00]
    pl=0.02425
    if p<pl:
        q=np.sqrt(-2*np.log(p)); return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p>1-pl:
        q=np.sqrt(-2*np.log(1-p)); return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q=p-0.5; r=q*q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def prec_at_k(y, score, frac):
    k = max(1, int(len(y) * frac))
    idx = np.argsort(-score)[:k]
    return float(y[idx].mean())


def main():
    df = pd.read_csv(os.path.join(HERE, "data", "processed", "sessions.csv"))
    df["month"] = df["date"].str[:7]
    tr, te = df[df.month.isin(TRAIN_MONTHS)], df[df.month.isin(TEST_MONTHS)]
    print(f"train={len(tr):,}  test={len(te):,}")

    top_vers = [clean_ver(x) for x in tr["ssh_ver"].map(clean_ver).value_counts().head(30).index]
    Xtr, Xte = build_features(tr, top_vers), build_features(te, top_vers)
    Xte = Xte.reindex(columns=Xtr.columns, fill_value=0)

    # ---------- Task A: engagement ----------
    ytr = (tr.intent != "bruteforce").astype(int).values
    yte = (te.intent != "bruteforce").astype(int).values
    base = yte.mean()
    rf = RandomForestClassifier(n_estimators=300, max_depth=None, class_weight="balanced",
                                n_jobs=4, random_state=0).fit(Xtr, ytr)
    gb = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08,
                                        class_weight="balanced", random_state=0).fit(Xtr, ytr)
    s_bci = 0.5 * (rf.predict_proba(Xte)[:, 1] + gb.predict_proba(Xte)[:, 1])
    s_proto = pd.Series(ytr).groupby(tr["proto"].values).mean().reindex(te["proto"].values).values  # proto-only
    s_nauth = te["n_auth"].values.astype(float)                                                       # n_auth-only

    methods_A = {"bci_ensemble": s_bci, "proto_only": s_proto, "nauth_only": s_nauth,
                 "prior_rate": np.full(len(yte), base)}
    rowsA = []
    for m, sc in methods_A.items():
        sc = np.nan_to_num(sc)
        rowsA.append({"method": m, "pr_auc": average_precision_score(yte, sc),
                      "roc_auc": roc_auc_score(yte, sc) if len(np.unique(sc)) > 1 else 0.5,
                      "p_at_1pct": prec_at_k(yte, sc, 0.01), "p_at_5pct": prec_at_k(yte, sc, 0.05),
                      "lift_at_1pct": prec_at_k(yte, sc, 0.01) / base})
    dfA = pd.DataFrame(rowsA); dfA.to_csv(os.path.join(OUT, "taskA_metrics.csv"), index=False)
    print("\nTask A (engagement):\n", dfA.round(3).to_string(index=False))

    # ---------- Task B: intent typing ----------
    yltr, ylte = tr.intent.values, te.intent.values
    clf = RandomForestClassifier(n_estimators=300, class_weight="balanced", n_jobs=4, random_state=0).fit(Xtr, yltr)
    pred = clf.predict(Xte)
    proto_map = tr.groupby("proto").intent.agg(lambda s: s.value_counts().index[0])
    pred_proto = te["proto"].map(proto_map).values
    maj = tr.intent.value_counts().index[0]
    rowsB = [{"method": "bci_rf", "macro_f1": f1_score(ylte, pred, average="macro", labels=INTENTS),
              "balanced_acc": balanced_accuracy_score(ylte, pred)},
             {"method": "proto_only", "macro_f1": f1_score(ylte, pred_proto, average="macro", labels=INTENTS),
              "balanced_acc": balanced_accuracy_score(ylte, pred_proto)},
             {"method": "majority", "macro_f1": f1_score(ylte, np.full(len(ylte), maj), average="macro", labels=INTENTS),
              "balanced_acc": balanced_accuracy_score(ylte, np.full(len(ylte), maj))}]
    perclass = f1_score(ylte, pred, average=None, labels=INTENTS)
    dfB = pd.DataFrame(rowsB); dfB.to_csv(os.path.join(OUT, "taskB_metrics.csv"), index=False)
    pd.DataFrame({"intent": INTENTS, "bci_f1": perclass}).to_csv(os.path.join(OUT, "taskB_perclass.csv"), index=False)
    print("\nTask B (intent typing):\n", dfB.round(3).to_string(index=False))
    print("per-class F1:", dict(zip(INTENTS, perclass.round(3))))

    # ---------- BCa CIs + hypotheses (fast vectorized metrics) ----------
    print(f"\nBootstrapping ({N_BOOT:,}) for hypotheses…")
    n = len(yte); idx_all = np.arange(n)
    jack_samp = RNG.choice(n, size=min(400, n), replace=False)
    def boot_stats(fn):
        bs = np.array([fn(RNG.integers(0, n, n)) for _ in range(N_BOOT)])  # index drawn per iter (low mem)
        jk = np.array([fn(np.concatenate([idx_all[:i], idx_all[i+1:]])) for i in jack_samp])
        return bs, jk
    # integer-code labels so the Task-B bootstrap runs on fast numeric arrays
    code = {c: i for i, c in enumerate(INTENTS)}
    yltei = np.array([code[x] for x in ylte]); predi = np.array([code[x] for x in pred])
    predpi = np.array([code.get(x, -1) for x in pred_proto]); LBL = list(range(len(INTENTS)))
    # H1: PR-AUC(bci) - base_rate
    f_h1 = lambda ix: fast_ap(yte[ix], s_bci[ix]) - yte[ix].mean()
    # H2: P@1%(bci) - base_rate  (lift>1)
    f_h2 = lambda ix: prec_at_k(yte[ix], s_bci[ix], 0.01) - yte[ix].mean()
    # H3: macroF1(bci) - macroF1(proto)  on Task B
    f_h3 = lambda ix: fast_macro_f1(yltei[ix], predi[ix], LBL) - fast_macro_f1(yltei[ix], predpi[ix], LBL)
    hyps = {}
    for name, fn, th in [("H1_prauc_vs_prior", f_h1, fast_ap(yte, s_bci) - base),
                         ("H2_p1pct_vs_base", f_h2, prec_at_k(yte, s_bci, 0.01) - base),
                         ("H3_macrof1_vs_proto", f_h3, rowsB[0]["macro_f1"] - rowsB[1]["macro_f1"])]:
        bs, jk = boot_stats(fn)
        lo, hi = bca_ci(bs, th, jk)
        hyps[name] = {"delta": round(float(th), 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4),
                      "supported": bool(lo > 0)}
        print(f"  {name}: delta={th:.4f} CI=[{lo:.4f},{hi:.4f}] supported={lo>0}")

    summary = {"n_train": int(len(tr)), "n_test": int(len(te)), "test_base_rate": round(float(base), 4),
               "n_boot": N_BOOT, "train_months": sorted(TRAIN_MONTHS), "test_months": sorted(TEST_MONTHS),
               "taskA": rowsA, "taskB": rowsB,
               "taskB_perclass": dict(zip(INTENTS, [round(float(x), 4) for x in perclass])),
               "hypotheses": hyps}
    json.dump(summary, open(os.path.join(OUT, "hypothesis_summary.json"), "w"), indent=2)
    pd.DataFrame([{"metric": k, **v} for k, v in hyps.items()]).to_csv(os.path.join(OUT, "primary_results.csv"), index=False)
    print(f"\nFrozen -> {OUT}")
    print("All hypotheses supported:", all(h["supported"] for h in hyps.values()))


if __name__ == "__main__":
    main()
