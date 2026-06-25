#!/usr/bin/env python3
"""Render the patent figures (FIG. 1-7) as clean block/flow diagrams."""
import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(OUT, exist_ok=True)
INK, ACC, FILL, MUT = "#0f172a", "#2563eb", "#eef2ff", "#64748b"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})


def fig(w=7.2, h=4.6):
    f, ax = plt.subplots(figsize=(w, h)); ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.axis("off"); return f, ax

def box(ax, x, y, w, h, text, fill=FILL, edge=ACC, fs=9, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=2.2",
                 linewidth=1.3, edgecolor=edge, facecolor=fill, mutation_aspect=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=INK,
            fontsize=fs, fontweight="bold" if bold else "normal", wrap=True)

def arrow(ax, x1, y1, x2, y2, color=MUT, label=None, style="-|>"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14,
                 linewidth=1.4, color=color, shrinkA=2, shrinkB=2))
    if label:
        ax.text((x1 + x2) / 2 + 2, (y1 + y2) / 2, label, fontsize=7.5, color=MUT, ha="left", va="center")

def vflow(ax, items, x=28, w=44, top=92, gap=4, bh=10, title=None):
    y = top
    centers = []
    for i, t in enumerate(items):
        box(ax, x, y - bh, w, bh, t)
        centers.append(y - bh / 2)
        if i < len(items) - 1:
            arrow(ax, x + w / 2, y - bh, x + w / 2, y - bh - gap)
        y -= bh + gap
    return centers, x, w


def fig1():
    f, ax = fig(7.4, 6.4)
    ax.text(50, 97, "FIG. 1 — Closed-loop deception platform", ha="center", fontsize=10, fontweight="bold", color=INK)
    items = ["Threat-Intelligence Ingestion", "AI Decision Engine  (policy-aware, explainable)",
             "Honeypot Orchestrator", "Dynamic Configuration Manager  +  Deception Randomization",
             "Behavioral-Cognitive Intent Model", "Real-Time Monitoring & Alerting",
             "Threat-Intelligence Logger & Correlation"]
    centers, x, w = vflow(ax, items, x=22, w=56, top=90, gap=3.5, bh=8.5)
    # policy integrator on the left, feedback on the right
    box(ax, 2, 40, 14, 22, "Policy\nIntegrator\n(guardrails)", fill="#fef3c7", edge="#d97706", fs=8)
    arrow(ax, 16, 51, 22, 78, color="#d97706"); arrow(ax, 16, 51, 22, 46, color="#d97706")
    arrow(ax, 78, centers[-1], 92, centers[-1]); arrow(ax, 92, centers[-1], 92, centers[1])
    arrow(ax, 92, centers[1], 78, centers[1], label="feedback")
    f.savefig(f"{OUT}/fig1_system.png", dpi=160, bbox_inches="tight"); plt.close(f)


def fig2():
    f, ax = fig(7.2, 4.2)
    ax.text(50, 95, "FIG. 2 — End-to-end closed loop", ha="center", fontsize=10, fontweight="bold", color=INK)
    steps = ["Ingest", "Decide", "Deploy", "Configure\n& Randomize", "Monitor &\nInfer Intent", "Alert &\nCorrelate"]
    n = len(steps); x0, w, y = 4, 13, 50
    cx = []
    for i, s in enumerate(steps):
        x = x0 + i * (w + 2.5)
        box(ax, x, y, w, 16, s, fs=8.5); cx.append(x + w / 2)
        if i < n - 1:
            arrow(ax, x + w, y + 8, x + w + 2.5, y + 8)
    arrow(ax, cx[-1], y, cx[-1], 22); arrow(ax, cx[-1], 22, cx[0], 22)
    arrow(ax, cx[0], 22, cx[0], y, label="feed back")
    f.savefig(f"{OUT}/fig2_loop.png", dpi=160, bbox_inches="tight"); plt.close(f)


def fig3():
    f, ax = fig(7.2, 4.6)
    ax.text(50, 96, "FIG. 3 — Deception-surface randomization", ha="center", fontsize=10, fontweight="bold", color=INK)
    box(ax, 4, 40, 24, 20, "Randomization\nSampler\n(per deployment)", fill="#eef2ff", edge=ACC, bold=True, fs=8.5)
    box(ax, 4, 8, 24, 14, "Fingerprint\nRegistry\n(diversify away)", fill="#f1f5f9", edge=MUT, fs=8)
    arrow(ax, 16, 40, 16, 22, color=MUT, style="<|-|>")
    dims = ["OS fingerprint", "Open-port set", "Service banner", "Version strings",
            "Error / prompt strings", "Response timing", "Emulated vulnerabilities"]
    for i, d in enumerate(dims):
        y = 86 - i * 11
        box(ax, 56, y - 8, 40, 8.5, d, fill="#ffffff", edge=ACC, fs=8)
        arrow(ax, 28, 50, 56, y - 4)
    ax.text(86, 6, "no two decoys share a fingerprint", fontsize=7.5, color=MUT, ha="center", style="italic")
    f.savefig(f"{OUT}/fig3_randomize.png", dpi=160, bbox_inches="tight"); plt.close(f)


def fig4():
    f, ax = fig(7.2, 4.0)
    ax.text(50, 94, "FIG. 4 — Behavioral-cognitive intent inference", ha="center", fontsize=10, fontweight="bold", color=INK)
    steps = ["Early, pre-action\nfeatures\n(auth structure,\nclient, timing)",
             "Trained\nclassifier", "Engagement\nlikelihood  +\nintent class",
             "Adapt engaged decoy\n& bias next deployment"]
    x0, w, y = 4, 21, 38
    cx = []
    for i, s in enumerate(steps):
        x = x0 + i * (w + 3)
        box(ax, x, y, w, 26, s, fs=8); cx.append(x + w / 2)
        if i < len(steps) - 1:
            arrow(ax, x + w, y + 13, x + w + 3, y + 13)
    ax.text(50, 80, "(post-action / command features deliberately excluded — enables EARLY inference)",
            ha="center", fontsize=7.5, color=MUT, style="italic")
    f.savefig(f"{OUT}/fig4_intent.png", dpi=160, bbox_inches="tight"); plt.close(f)


def fig5():
    f, ax = fig(7.2, 4.8)
    ax.text(50, 96, "FIG. 5 — Self-healing vulnerability mutation", ha="center", fontsize=10, fontweight="bold", color=INK)
    box(ax, 30, 80, 40, 11, "Real-Time Behavior Analyzer\n(assess exploit attempt)", fs=8.5)
    arrow(ax, 50, 80, 50, 74)
    box(ax, 26, 62, 48, 11, "Mutation Decision Engine\n(classify attack)", fill="#eef2ff", edge=ACC, bold=True, fs=8.5)
    opts = [("Heal\n(simulate patch /\nshutdown)", 4), ("Swap\n(change version /\nconfig)", 38), ("Introduce\n(new port /\nprotocol)", 72)]
    for t, x in opts:
        box(ax, x, 34, 24, 16, t, fill="#ffffff", edge="#059669", fs=8)
        arrow(ax, 50, 62, x + 12, 50, color="#059669")
        arrow(ax, x + 12, 34, 50, 22, color=MUT)
    box(ax, 26, 8, 48, 12, "Live Configuration Modifier\n(ports, banners, FS, creds — no session reset)", fill="#fef3c7", edge="#d97706", fs=8)
    f.savefig(f"{OUT}/fig5_selfheal.png", dpi=160, bbox_inches="tight"); plt.close(f)


def fig6():
    f, ax = fig(7.2, 4.6)
    ax.text(50, 96, "FIG. 6 — On-demand, trigger-based lifecycle", ha="center", fontsize=10, fontweight="bold", color=INK)
    trig = ["Threat feed", "SIEM alert", "Behavioral anomaly", "Manual / API"]
    for i, t in enumerate(trig):
        box(ax, 2, 80 - i * 11, 24, 8.5, t, fill="#ffffff", edge=MUT, fs=8)
        arrow(ax, 26, 84 - i * 11, 34, 60)
    box(ax, 34, 54, 30, 12, "Trigger Evaluation\nnormalize · suppress FP\n· enrich", fill="#eef2ff", edge=ACC, fs=8)
    arrow(ax, 64, 60, 72, 60)
    box(ax, 72, 54, 24, 12, "Threat scoring\n≥ threshold?", fill="#fef3c7", edge="#d97706", fs=8)
    arrow(ax, 84, 54, 84, 40, label="yes")
    box(ax, 64, 26, 40, 12, "Provision from Template Library\n(SSH/RDP/FTP/HTTP · K8s/Docker/IaC)", fs=8)
    arrow(ax, 84, 26, 84, 14)
    box(ax, 64, 2, 40, 10, "Teardown Controller\n(retire on lifecycle / intel-value end)", fill="#fee2e2", edge="#dc2626", fs=8)
    f.savefig(f"{OUT}/fig6_ondemand.png", dpi=160, bbox_inches="tight"); plt.close(f)


def fig7():
    f, ax = fig(7.2, 3.8)
    ax.text(50, 93, "FIG. 7 — Policy guardrails (two-stage enforcement)", ha="center", fontsize=10, fontweight="bold", color=INK)
    box(ax, 6, 45, 36, 30, "DECISION TIME\n(AI Decision Engine)\n\nregion · template · budget\nexposure · retention", fill="#eef2ff", edge=ACC, fs=8.5)
    box(ax, 58, 45, 36, 30, "EXECUTION TIME\n(Orchestrator)\n\nre-check before provision;\nreject + log on violation", fill="#fef3c7", edge="#d97706", fs=8.5)
    arrow(ax, 42, 60, 58, 60, label="instruction")
    box(ax, 30, 8, 40, 14, "Policy store\n(tenant + global rules)", fill="#f1f5f9", edge=MUT, fs=8)
    arrow(ax, 40, 22, 24, 45, color=MUT); arrow(ax, 60, 22, 76, 45, color=MUT)
    f.savefig(f"{OUT}/fig7_policy.png", dpi=160, bbox_inches="tight"); plt.close(f)


for fn in (fig1, fig2, fig3, fig4, fig5, fig6, fig7):
    fn()
print("figures ->", OUT)
print(sorted(os.listdir(OUT)))
