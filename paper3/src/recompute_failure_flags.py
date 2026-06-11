#!/usr/bin/env python3
"""Recompute pre-registered failure flags with the correct aggregation unit.

The pre-registered protocol (paper Eq. 1): a (condition, task, method)
configuration is flagged as a negative result if

    AP(method) - AP(M1) < 0.05  AND  P@k(method) - P@k(M1) < 0.05

in at least ceil(2/3 * n_seeds) = 2 of 3 seeds.

An earlier pipeline version aggregated per (condition, seed), treating each
seed-suffixed condition id (e.g. c_base_seed42) as a separate condition.
This script strips the seed suffix and applies the protocol per true
(condition, task, method) group of 3 seeds, exactly as pre-registered.
"""

import csv
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "primary_full_v1" / "primary_results.csv"

DELTA = 0.05


def strip_seed(condition_id: str) -> str:
    return re.sub(r"_seed\d+$", "", condition_id)


def main() -> None:
    rows = list(csv.DictReader(open(RESULTS)))
    # index M1 (rule baseline) per (condition, task, seed)
    rule = {}
    for r in rows:
        if r["method_id"] == "M1_rule":
            rule[(strip_seed(r["condition_id"]), r["task_id"], r["seed"])] = (
                float(r["ap"]), float(r["pk"]))

    # group non-M1 runs per (condition, task, method)
    groups = defaultdict(list)
    for r in rows:
        if r["method_id"] == "M1_rule":
            continue
        if r["error"]:
            continue
        cond = strip_seed(r["condition_id"])
        groups[(cond, r["task_id"], r["method_id"])].append(r)

    flagged = total = 0
    per_method = defaultdict(lambda: [0, 0])  # method -> [flagged, total]
    per_cell = {}  # (method, task) -> [flagged, total]
    for (cond, task, method), runs in sorted(groups.items()):
        n_seeds = len(runs)
        need = math.ceil(2 / 3 * n_seeds)
        n_fail_seeds = 0
        for r in runs:
            rap, rpk = rule[(cond, task, r["seed"])]
            ap, pk = float(r["ap"]), float(r["pk"])
            if (ap - rap < DELTA) and (pk - rpk < DELTA):
                n_fail_seeds += 1
        is_flagged = n_fail_seeds >= need
        total += 1
        per_method[method][1] += 1
        cell = per_cell.setdefault((method, task), [0, 0])
        cell[1] += 1
        if is_flagged:
            flagged += 1
            per_method[method][0] += 1
            cell[0] += 1

    print(f"Overall: {flagged}/{total} = {100*flagged/total:.1f}%")
    print("\nPer-method failure rates:")
    for m in sorted(per_method):
        f, t = per_method[m]
        print(f"  {m}: {f}/{t} = {100*f/t:.1f}%")

    print("\nPer-(method, task) cell rates (for fig2):")
    methods = sorted({m for m, _ in per_cell})
    tasks = sorted({t for _, t in per_cell})
    for m in methods:
        cells = []
        for t in tasks:
            if (m, t) in per_cell:
                f, n = per_cell[(m, t)]
                cells.append(f"{t}:{f}/{n}")
            else:
                cells.append(f"{t}:N/A")
        print(f"  {m}: " + "  ".join(cells))

    # AP stability (1 - CV across seeds) per method, over all (cond, task) groups
    print("\nAP stability (1 - CV across 3 seeds), mean per method:")
    stab = defaultdict(list)
    for r in rows:
        if r["error"]:
            continue
        cond = strip_seed(r["condition_id"])
        stab[(cond, r["task_id"], r["method_id"])].append(float(r["ap"]))
    per_method_stab = defaultdict(list)
    for (cond, task, method), aps in stab.items():
        mean = sum(aps) / len(aps)
        if mean == 0:
            continue
        var = sum((a - mean) ** 2 for a in aps) / len(aps)
        cv = math.sqrt(var) / mean
        per_method_stab[method].append(1 - cv)
    for m in sorted(per_method_stab):
        vals = per_method_stab[m]
        print(f"  {m}: mean {sum(vals)/len(vals):.3f}  min {min(vals):.3f}")


if __name__ == "__main__":
    main()
