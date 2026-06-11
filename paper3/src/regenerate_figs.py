#!/usr/bin/env python3
"""Regenerate fig1 (AP heatmap) and fig2 (failure-flag heatmap) with the
pre-registered per-(condition, task, method) aggregation and rows ordered
by mean AP (descending)."""

import csv
import math
import re
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "primary_full_v1" / "primary_results.csv"
DELTA = 0.05

METHOD_LABELS = {
    "M1_rule": "M1 Rule",
    "M2_hybrid": "M2 Hybrid",
    "M3_iforest": "M3 IForest",
    "M4_lof": "M4 LOF",
    "M5_ocsvm": "M5 OCSVM",
    "M6_linearae": "M6 Linear-AE",
    "M7_zscore": "M7 Z-score",
    "M8_graphif": "M8 Graph-IF",
}
TASKS = [f"T{i}" for i in range(1, 8)]


def strip_seed(cid):
    return re.sub(r"_seed\d+$", "", cid)


def main():
    rows = [r for r in csv.DictReader(open(RESULTS)) if not r["error"]]

    # mean AP per method x task, and overall mean AP per method (row order)
    ap_cells = defaultdict(list)
    for r in rows:
        ap_cells[(r["method_id"], r["task_id"])].append(float(r["ap"]))
    mean_ap_method = {}
    for m in METHOD_LABELS:
        vals = [v for (mm, t), vs in ap_cells.items() if mm == m for v in vs]
        mean_ap_method[m] = sum(vals) / len(vals)
    order = sorted(METHOD_LABELS, key=lambda m: -mean_ap_method[m])

    # failure flags per (condition, task, method)
    rule = {}
    for r in rows:
        if r["method_id"] == "M1_rule":
            rule[(strip_seed(r["condition_id"]), r["task_id"], r["seed"])] = (
                float(r["ap"]), float(r["pk"]))
    groups = defaultdict(list)
    for r in rows:
        if r["method_id"] != "M1_rule":
            groups[(strip_seed(r["condition_id"]), r["task_id"],
                    r["method_id"])].append(r)
    cell = defaultdict(lambda: [0, 0])  # (method, task) -> [flagged, n_conds]
    for (cond, task, method), runs in groups.items():
        need = math.ceil(2 / 3 * len(runs))
        nf = sum(1 for r in runs
                 if float(r["ap"]) - rule[(cond, task, r["seed"])][0] < DELTA
                 and float(r["pk"]) - rule[(cond, task, r["seed"])][1] < DELTA)
        cell[(method, task)][1] += 1
        if nf >= need:
            cell[(method, task)][0] += 1

    out_dirs = [ROOT / "manuscript" / "figures",
                ROOT / "submission" / "acm" / "figures",
                ROOT / "submission" / "ieee" / "figures"]

    # ---- fig1: AP heatmap -------------------------------------------------
    M = np.full((len(order), len(TASKS)), np.nan)
    for i, m in enumerate(order):
        for j, t in enumerate(TASKS):
            if (m, t) in ap_cells:
                M[i, j] = np.mean(ap_cells[(m, t)])
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
    masked = np.ma.masked_invalid(M)
    im = ax.imshow(masked, cmap="RdYlGn", vmin=0.3, vmax=1.0, aspect="auto")
    for i in range(len(order)):
        for j in range(len(TASKS)):
            if np.isnan(M[i, j]):
                ax.text(j, i, "N/A", ha="center", va="center",
                        color="gray", fontsize=9)
            else:
                ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center",
                        fontsize=9)
    ax.set_xticks(range(len(TASKS)), TASKS)
    ax.set_yticks(range(len(order)), [METHOD_LABELS[m] for m in order])
    ax.set_xlabel("Task")
    ax.set_title("Mean Average Precision by Method × Task\n"
                 "(all conditions and seeds; rows ordered by mean AP)")
    fig.colorbar(im, ax=ax, label="AP")
    fig.tight_layout()
    for d in out_dirs:
        fig.savefig(d / "fig1_ap_heatmap.pdf")
        fig.savefig(d / "fig1_ap_heatmap.png")
    plt.close(fig)

    # ---- fig2: failure-flag heatmap ---------------------------------------
    order_f = order  # same ordering, M1 row shown as baseline dashes
    F = np.full((len(order_f), len(TASKS)), np.nan)
    for i, m in enumerate(order_f):
        if m == "M1_rule":
            continue
        for j, t in enumerate(TASKS):
            if (m, t) in cell:
                f, n = cell[(m, t)]
                F[i, j] = f / n
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
    masked = np.ma.masked_invalid(F)
    im = ax.imshow(masked, cmap="RdYlGn_r", vmin=0.0, vmax=1.0, aspect="auto")
    for i, m in enumerate(order_f):
        for j, t in enumerate(TASKS):
            if m == "M1_rule":
                ax.text(j, i, "—", ha="center", va="center",
                        color="gray", fontsize=9)
            elif np.isnan(F[i, j]):
                ax.text(j, i, "N/A", ha="center", va="center",
                        color="gray", fontsize=9)
            else:
                color = "white" if F[i, j] > 0.6 else "black"
                ax.text(j, i, f"{100*F[i, j]:.0f}%", ha="center",
                        va="center", fontsize=9, color=color)
    ax.set_xticks(range(len(TASKS)), TASKS)
    ax.set_yticks(range(len(order_f)), [METHOD_LABELS[m] for m in order_f])
    ax.set_xlabel("Task")
    ax.set_title("Failure-Flag Rate by Method × Task\n"
                 "(fraction of 5 conditions flagged: Δ<0.05 vs. rule "
                 "in ≥2/3 seeds)")
    fig.colorbar(im, ax=ax, label="Failure Rate")
    fig.tight_layout()
    for d in out_dirs:
        fig.savefig(d / "fig2_failure_heatmap.pdf")
        fig.savefig(d / "fig2_failure_heatmap.png")
    plt.close(fig)
    print("done; row order:", [METHOD_LABELS[m] for m in order],
          {METHOD_LABELS[m]: round(mean_ap_method[m], 3) for m in order})


if __name__ == "__main__":
    main()
