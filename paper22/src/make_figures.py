#!/usr/bin/env python3
"""Figures for the ENSES (ESWA) paper, from frozen results + the trained model."""
import os, json, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import run_eval as R, enses as E

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "results", "primary_v1")
FIG = os.path.join(HERE, "submission", "ieee", "figures"); os.makedirs(FIG, exist_ok=True)
S = json.load(open(os.path.join(RES, "primary_summary.json")))
INK, ACC, GRY, GRN, AMB = "#0f172a", "#2563eb", "#94a3b8", "#059669", "#d97706"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

# ── FIG 1: architecture (neuro-symbolic, glass-box) ──
def fig_arch():
    f, ax = plt.subplots(figsize=(7.4, 4.3)); ax.set_xlim(0,100); ax.set_ylim(0,100); ax.axis("off")
    def box(x,y,w,h,t,fill="#eef2ff",ec=ACC,fs=8.2,bold=False):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.5,rounding_size=2",lw=1.3,ec=ec,fc=fill))
        ax.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=fs,color=INK,fontweight="bold" if bold else "normal")
    def arr(x1,y1,x2,y2,c=GRY):
        ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=12,lw=1.3,color=c))
    box(2,78,30,16,"Real public data\nEPSS · KEV · CWE · descriptions\n(203,174 CVEs)",fill="#f1f5f9",ec=GRY,fs=7.6)
    box(2,56,30,16,"Smart-city / IIoT / health\nasset estate (6 classes,\ncriticality) + diff. privacy",fill="#f1f5f9",ec=GRY,fs=7.6)
    box(38,74,28,20,"Symbolic tier (KG + rules)\nCVE→CWE→class→tactic\n→asset · metadata relevance",fill="#eef2ff",ec=ACC,fs=7.8)
    box(38,50,28,20,"Neural tier (RAG)\nnomic-embed-text\ndescription ↔ asset profile",fill="#ecfdf5",ec=GRN,fs=7.8)
    box(70,58,28,28,"Glass-box inference\nengine\nadditive fusion +\nexploit×crit×relevance",fill="#fffbeb",ec=AMB,fs=8,bold=True)
    box(70,24,28,18,"Prioritized (asset,CVE)\nlist + per-decision\nexplanation",fill="#eef2ff",ec=ACC,fs=7.8)
    arr(32,86,38,84); arr(32,64,38,60); arr(66,84,70,75); arr(66,60,70,68); arr(84,58,84,42)
    arr(84,24,84,16,GRN); ax.add_patch(FancyArrowPatch((70,30),(38,30),arrowstyle="-|>",mutation_scale=11,lw=1.2,color=GRN,connectionstyle="arc3,rad=-0.25"))
    ax.text(54,26,"explanations feed analyst review",fontsize=7,color=GRN,style="italic")
    ax.text(50,97,"Fig. 1. ENSES architecture: symbolic + neural tiers fused by a glass-box engine.",ha="center",fontsize=9,fontweight="bold")
    f.savefig(f"{FIG}/fig1_arch.pdf",bbox_inches="tight"); f.savefig(f"{FIG}/fig1_arch.png",dpi=160,bbox_inches="tight"); plt.close(f)

# ── FIG 2: methods comparison ──
def fig_methods():
    order=["enses","xgb","abl_noneu","epss","kevfirst","random"]
    lab=["ENSES\n(ours)","XGBoost\nensemble","ENSES\n−neural","EPSS\n-only","KEV\n-first","Random"]
    wp=[S["methods"][m]["wp@100"] for m in order]; nd=[S["methods"][m]["ndcg@100"] for m in order]
    x=np.arange(len(order)); w=0.38
    f,ax=plt.subplots(figsize=(7.0,3.6))
    b1=ax.bar(x-w/2,wp,w,label="Harm-weighted P@100",color=ACC)
    b2=ax.bar(x+w/2,nd,w,label="NDCG@100",color=GRN)
    for b in list(b1)+list(b2): ax.text(b.get_x()+b.get_width()/2,b.get_height()+.012,f"{b.get_height():.2f}",ha="center",fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(lab,fontsize=8); ax.set_ylim(0,1.0); ax.set_ylabel("score")
    ax.legend(fontsize=8,frameon=False); ax.spines[["top","right"]].set_visible(False)
    ax.set_title("Fig. 2. Prioritization quality on real EPSS/KEV data (25 seeds).",fontsize=9)
    f.savefig(f"{FIG}/fig2_methods.pdf",bbox_inches="tight"); f.savefig(f"{FIG}/fig2_methods.png",dpi=160,bbox_inches="tight"); plt.close(f)

# ── FIG 3: ablation ──
def fig_ablation():
    order=["enses","abl_nokg","abl_noneu","abl_nocrit"]; lab=["Full ENSES","− knowledge\ngraph","− neural\ntier","− asset\ncriticality"]
    wp=[S["methods"][m]["wp@100"] for m in order]
    f,ax=plt.subplots(figsize=(5.6,3.4)); col=[ACC,AMB,GRN,"#dc2626"]
    b=ax.bar(lab,wp,color=col,width=0.62)
    for bb in b: ax.text(bb.get_x()+bb.get_width()/2,bb.get_height()+.012,f"{bb.get_height():.2f}",ha="center",fontsize=8)
    ax.set_ylim(0,1.0); ax.set_ylabel("harm-weighted P@100"); ax.spines[["top","right"]].set_visible(False)
    ax.set_title("Fig. 3. Ablation: each neuro-symbolic tier is necessary.",fontsize=9)
    f.savefig(f"{FIG}/fig3_ablation.pdf",bbox_inches="tight"); f.savefig(f"{FIG}/fig3_ablation.png",dpi=160,bbox_inches="tight"); plt.close(f)

# ── FIG 4: worked per-decision explanation (glass-box additive contributions) ──
def fig_explain():
    classes, feats = R.build()
    pairs = R.make_fleet(feats, classes, seed=3); train = R.make_fleet(feats, classes, seed=103)
    pred, m, names, mu, sd = R.enses_learned(train, pairs, classes, frozenset(), return_model=True)
    Xte,_ = R.featurize(pairs, classes, frozenset()); Z=(Xte-mu)/sd
    i = int(np.argmax(pred))  # the top-prioritized pair
    contrib = m.coef_ * Z[i]
    o = np.argsort(np.abs(contrib))
    nm=[names[j] for j in o]; cv=[contrib[j] for j in o]
    f,ax=plt.subplots(figsize=(6.2,3.8))
    col=[ACC if c>=0 else "#dc2626" for c in cv]
    ax.barh(range(len(cv)),cv,color=col)
    ax.set_yticks(range(len(cv))); ax.set_yticklabels(nm,fontsize=8)
    ax.axvline(0,color=INK,lw=0.8); ax.set_xlabel("contribution to risk score")
    ax.spines[["top","right"]].set_visible(False)
    a,ci,cr,f0 = pairs[i][0],pairs[i][1],pairs[i][2],pairs[i][3]
    ax.set_title(f"Fig. 4. Glass-box explanation for the top-ranked decision\n({f0['cve']} on a tier-{cr} {classes[ci].replace('_',' ')} asset)",fontsize=8.4)
    f.savefig(f"{FIG}/fig4_explain.pdf",bbox_inches="tight"); f.savefig(f"{FIG}/fig4_explain.png",dpi=160,bbox_inches="tight"); plt.close(f)

for fn in (fig_arch, fig_methods, fig_ablation, fig_explain):
    fn(); print("ok", fn.__name__)
print("figures ->", FIG)
