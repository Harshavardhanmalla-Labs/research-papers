#!/usr/bin/env python3
"""Figures for the tamper-evident provenance paper, from frozen results."""
import os, json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "results", "provenance_v1")
FIG = os.path.join(HERE, "paper", "submission", "ieee", "figures"); os.makedirs(FIG, exist_ok=True)
d = json.load(open(os.path.join(RES, "provenance_summary.json")))
BLUE, GRAY, RED, GREEN = "#2563eb", "#9aa3af", "#dc2626", "#059669"

NICE = {"modify_field": "Modify field", "reorder": "Reorder", "delete_middle": "Delete (interior)",
        "truncate_tail": "Truncate tail", "insert": "Insert forged", "weight_rollback": "Weight rollback",
        "feed_forge": "Feed-version forge", "wholesale_replace": "Wholesale replace"}

# Fig 1 — detection heatmap (attack x scheme/attacker)
det = d["detection"]
cols = ["weak_baseline", "weak_augmented", "strong_baseline", "strong_augmented"]
collab = ["Naive chain\n(weak adv.)", "Ledger\n(weak adv.)", "Naive chain\n(insider)", "Ledger\n(insider)"]
M = np.array([[r[c] for c in cols] for r in det])
fig, ax = plt.subplots(figsize=(6.4, 4.2))
ax.imshow(M, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(len(cols))); ax.set_xticklabels(collab, fontsize=8)
ax.set_yticks(range(len(det))); ax.set_yticklabels([NICE[r["attack"]] for r in det], fontsize=8)
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center", fontsize=8,
                color="white" if M[i, j] < 0.5 else "#0f172a", fontweight="bold")
ax.set_title("Tamper-detection rate by attack, scheme, and adversary", fontsize=10)
plt.tight_layout(); plt.savefig(f"{FIG}/fig1_detection.pdf"); plt.savefig(f"{FIG}/fig1_detection.png", dpi=150); plt.close()

# Fig 2 — verification scaling + constant space overhead
ovh = d["overhead"]
n = [r["n_records"] for r in ovh]
vb = [r["verify_baseline_s"] * 1000 for r in ovh]
va = [r["verify_augmented_s"] * 1000 for r in ovh]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(8, 3.4))
a1.plot(n, vb, "o-", color=GRAY, lw=2, label="naive chain")
a1.plot(n, va, "o-", color=BLUE, lw=2, label="signed-checkpoint ledger")
a1.set_xlabel("audit records"); a1.set_ylabel("full verification (ms)")
a1.set_title("Verification scales linearly", fontsize=10); a1.legend(fontsize=8, frameon=False)
a1.spines[["top", "right"]].set_visible(False)
ov = [r["checkpoint_overhead_pct"] for r in ovh]
a2.bar([str(x) for x in n], ov, color=GREEN, width=0.6)
a2.set_xlabel("audit records"); a2.set_ylabel("checkpoint space overhead (%)")
a2.set_ylim(0, 1.0); a2.set_title("Space overhead is near-constant", fontsize=10)
for i, v in enumerate(ov):
    a2.text(i, v + 0.02, f"{v:.2f}%", ha="center", fontsize=8)
a2.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(f"{FIG}/fig2_overhead.pdf"); plt.savefig(f"{FIG}/fig2_overhead.png", dpi=150); plt.close()
print("figures ->", FIG)
print("append throughput (rec/s):", [r["append_throughput_rec_s"] for r in ovh])
print("verify augmented (ms):", [round(x, 1) for x in va])
