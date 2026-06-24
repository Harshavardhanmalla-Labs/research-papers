#!/usr/bin/env python3
"""Figures + attacker-archetype clustering for BCI-Honey, from the real frozen data.

Reproduces the model (same seed as run_evaluation.py) to obtain scores / importances
for plotting, then renders publication figures into figures/ and writes
results/primary_v1/archetypes.csv.
"""
import os, json, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import roc_curve, auc
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(HERE, "figures"); os.makedirs(FIG, exist_ok=True)
RES = os.path.join(HERE, "results", "primary_v1")
TRAIN = {"2019-05","2019-06","2019-07","2019-08","2019-09","2019-10","2019-11"}
TEST = {"2019-12","2020-01","2020-02"}
EARLY = ["n_enc","n_kex","n_mac","n_key","has_hassh","n_auth","n_auth_ok","n_distinct_creds","max_pw_len","empty_pw","common_user","hour"]
INTENTS = ["bruteforce","tunneling","execution","malware_delivery"]
NICE = {"bruteforce":"Brute-force\n(T1110)","tunneling":"Tunneling\n(T1090)","execution":"Execution\n(T1059)","malware_delivery":"Malware\n(T1105)"}
BLUE, GRAY, AMBER = "#2563eb", "#9aa3af", "#d97706"
import re
clean = lambda s: (re.match(r"^b?'?(.*?)'?$", str(s)).group(1))[:40] or "none"

def feats(df, vers):
    X = df[EARLY].fillna(0).copy()
    X["proto_telnet"] = (df.proto=="telnet").astype(int)
    v = df.ssh_ver.map(clean)
    for tv in vers: X[f"ver_{tv}"] = (v==tv).astype(int)
    X["ver_other"] = (~v.isin(vers)).astype(int)
    return X

def main():
    df = pd.read_csv(os.path.join(HERE,"data","processed","sessions.csv"))
    df["month"]=df.date.str[:7]
    tr,te = df[df.month.isin(TRAIN)], df[df.month.isin(TEST)]
    vers=[clean(x) for x in tr.ssh_ver.map(clean).value_counts().head(30).index]
    Xtr,Xte = feats(tr,vers), feats(te,vers); Xte=Xte.reindex(columns=Xtr.columns,fill_value=0)
    ytr=(tr.intent!="bruteforce").astype(int).values; yte=(te.intent!="bruteforce").astype(int).values
    rf=RandomForestClassifier(n_estimators=300,class_weight="balanced",n_jobs=4,random_state=0).fit(Xtr,ytr)
    gb=HistGradientBoostingClassifier(max_iter=300,learning_rate=0.08,class_weight="balanced",random_state=0).fit(Xtr,ytr)
    s=0.5*(rf.predict_proba(Xte)[:,1]+gb.predict_proba(Xte)[:,1])
    base=yte.mean()

    # Fig 1 — intent distribution (real)
    d=df.intent.value_counts().reindex(INTENTS)
    fig,ax=plt.subplots(figsize=(6,3.4))
    bars=ax.bar([NICE[i] for i in INTENTS], d.values, color=[GRAY,BLUE,AMBER,"#dc2626"])
    ax.set_yscale("log"); ax.set_ylabel("sessions (log)")
    for b,v in zip(bars,d.values): ax.text(b.get_x()+b.get_width()/2, v*1.1, f"{v:,}\n{100*v/len(df):.1f}%", ha="center", fontsize=8)
    ax.set_title("Real attacker-intent distribution (379k honeypot sessions)",fontsize=10)
    ax.spines[["top","right"]].set_visible(False); plt.tight_layout(); plt.savefig(f"{FIG}/fig1_intent_distribution.png",dpi=150); plt.close()

    # Fig 2 — ROC + precision@k lift
    fpr,tpr,_=roc_curve(yte,s); proto_rate=tr.groupby("proto")["intent"].apply(lambda z:(z!="bruteforce").mean())
    sp=te.proto.map(proto_rate).fillna(0).values; fpr2,tpr2,_=roc_curve(yte,sp)
    fig,(a1,a2)=plt.subplots(1,2,figsize=(8,3.5))
    a1.plot(fpr,tpr,color=BLUE,lw=2,label=f"BCI ensemble (AUC={auc(fpr,tpr):.3f})")
    a1.plot(fpr2,tpr2,color=AMBER,lw=1.5,label=f"protocol-only (AUC={auc(fpr2,tpr2):.3f})")
    a1.plot([0,1],[0,1],"--",color=GRAY,lw=1,label="chance")
    a1.set_xlabel("false positive rate"); a1.set_ylabel("true positive rate"); a1.set_title("Engagement ROC",fontsize=10); a1.legend(fontsize=8,frameon=False)
    ks=np.array([0.005,0.01,0.02,0.05,0.1]); lifts=[]
    for k in ks:
        kk=max(1,int(len(yte)*k)); idx=np.argsort(-s)[:kk]; lifts.append(yte[idx].mean()/base)
    a2.plot(ks*100,lifts,"o-",color=BLUE,lw=2); a2.axhline(1,ls="--",color=GRAY,lw=1,label="no lift")
    a2.set_xlabel("% sessions flagged (top-k)"); a2.set_ylabel("lift over base engagement"); a2.set_title("Early-flagging lift",fontsize=10); a2.legend(fontsize=8,frameon=False)
    for ax in (a1,a2): ax.spines[["top","right"]].set_visible(False)
    plt.tight_layout(); plt.savefig(f"{FIG}/fig2_roc_lift.png",dpi=150); plt.close()

    # Fig 3 — feature importance (top early signals)
    imp=pd.Series(rf.feature_importances_,index=Xtr.columns).sort_values(ascending=False).head(12)[::-1]
    fig,ax=plt.subplots(figsize=(6,3.6)); ax.barh(range(len(imp)),imp.values,color=BLUE)
    ax.set_yticks(range(len(imp))); ax.set_yticklabels(imp.index,fontsize=8); ax.set_xlabel("Gini importance")
    ax.set_title("Top early-phase behavioral-cognitive features",fontsize=10)
    ax.spines[["top","right"]].set_visible(False); plt.tight_layout(); plt.savefig(f"{FIG}/fig3_feature_importance.png",dpi=150); plt.close()

    # Fig 4 — attacker archetypes via KMeans on behavioral-cognitive profile
    Z=StandardScaler().fit_transform(Xtr[EARLY].values)
    km=KMeans(n_clusters=5,n_init=10,random_state=0).fit(Z)
    tr2=tr.copy(); tr2["cluster"]=km.labels_
    arche=tr2.groupby("cluster").agg(n=("intent","size"),engaged=("intent",lambda z:(z!="bruteforce").mean()),
        dom_intent=("intent",lambda z:z.value_counts().index[0]),
        telnet=("proto",lambda z:(z=="telnet").mean()),hassh=("has_hassh","mean"),n_auth=("n_auth","mean"))
    arche.to_csv(os.path.join(RES,"archetypes.csv"))
    P=PCA(n_components=2,random_state=0).fit_transform(Z[:8000]); lab=km.labels_[:8000]
    fig,ax=plt.subplots(figsize=(5.6,4.2))
    sc=ax.scatter(P[:,0],P[:,1],c=lab,cmap="tab10",s=4,alpha=0.5)
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2"); ax.set_title("Attacker behavioral-cognitive archetypes (k=5)",fontsize=10)
    ax.spines[["top","right"]].set_visible(False); plt.tight_layout(); plt.savefig(f"{FIG}/fig4_archetypes.png",dpi=150); plt.close()

    print("figures ->",FIG)
    print(arche.round(3).to_string())

if __name__=="__main__":
    main()
