# Paper 9 — Pre-Registration Protocol

**Working title:** Self-Trajectory Evaluation: Is HygienePrio's
Capacity-Driven Collapse Intrinsic or Selection-Policy-Induced?

**Authors:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**Date locked:** 2026-06-05 (before any self-trajectory result was inspected)
**Builds on:** Papers 4-8 of the VulnPrio sequence.

---

## 1. Motivation

Papers 5--8 share one acknowledged internal-validity threat: at every
window of every cell, fleet evolution is driven by HygienePrio-full's
top-$K$ selection with the calibrated Paper~4 weights. EPSS-only,
HRS-only, CVSS-only, and Random are scored against the HygienePrio-driven
evolving backlog rather than against their own counterfactual trajectories.

In particular, Paper~6 reported that HygienePrio-full's W6 P@50 collapses
at $K \in \{100, 200\}$ via high-HRS-tail exhaustion. The collapse was
measured on the HygienePrio-driven trajectory. \textbf{We do not know
whether the same collapse would occur if HygienePrio's own selection were
not the policy draining the high-HRS tail.} An EPSS-only-driven
trajectory would drain the high-EPSS tail instead; on that trajectory,
HygienePrio's W6 P@50 could be different (the high-HRS tail would survive
longer because EPSS-only's selection is HRS-blind).

This paper isolates the question: \textit{how much of the apparent
behaviour in Papers 5--8 is intrinsic to the scoring decision, and how
much is induced by which method drives the trajectory?}

## 2. Research questions

- **RQ1.** Does HygienePrio-full's W6 P@50 collapse at $K = 200$ survive
  when EPSS-only or CVSS-only drives the trajectory?
- **RQ2.** Is EPSS-only's universal decay (Paper~6) sharper, equal to, or
  shallower on its own self-trajectory?
- **RQ3.** Does HygienePrio-full's per-pair dominance over EPSS-only
  (Paper~6's $96\%$ at canonical cell) survive on \textit{each} method's
  own trajectory?

## 3. Hypotheses

| ID | Statement | Decision rule |
|----|-----------|---------------|
| H1 | HygienePrio's W6 P@50 collapse at $K = 200$ is intrinsic, not selection-policy-induced: HygienePrio's W6 P@50 on a non-HygienePrio-driven trajectory is within $\pm 0.05$ of its W6 P@50 on its own trajectory. | Supported if for at least one non-HP driving method $m'$, $|\mathrm{P@50}^{\mathrm{HP}}_{w=6}(T_{m'}) - \mathrm{P@50}^{\mathrm{HP}}_{w=6}(T_{\mathrm{HP}})| \leq 0.05$. |
| H2 | EPSS-only's W6 decay is sharper on its own trajectory than on HygienePrio's: $\mathrm{P@50}^{\mathrm{EPSS}}_{w=6}(T_{\mathrm{EPSS}}) < \mathrm{P@50}^{\mathrm{EPSS}}_{w=6}(T_{\mathrm{HP}})$. | Supported at $K = 50$ if the inequality holds in the cell mean with non-overlapping bootstrap CIs. |
| H3 | HygienePrio's per-pair dominance over EPSS-only is preserved on EPSS-only's own trajectory: cell-fraction $(\text{HP} > \text{EPSS} \mid T_{\mathrm{EPSS}}) \geq 0.75$ at $K = 50$ and $\geq 0.50$ at $K = 200$. | Supported if both thresholds met. |

**Stop rules:**
- If H1 is rejected (selection-policy effect dominates), the abstract is
  rewritten to qualify Paper~6's H4-collapse interpretation before the
  discussion is drafted.
- If H3 is rejected (HP does not dominate on EPSS-driven trajectory),
  Paper~5's ``$96\%$ per-pair dominance'' claim is qualified as
  trajectory-conditional in our retroactive commentary.

## 4. Cell grid (locked)

| Axis | Values |
|------|--------|
| Capacity $K$ | $\{50, 200\}$ (low control + Paper~6 collapse cell) |
| Arrival rate $\lambda$ | 3 (fixed; matches Papers 7--8) |
| Windows $W$ | 6 |
| Driving methods | HygienePrio-full, EPSS-only, HRS-only, CVSS-only, Random |
| Scoring methods (evaluated at every window) | same set, 5 methods |
| Seeds | 25 (105--129; identical to Papers 5--8 evaluation set) |

Total rows: $2 \text{ cells} \times 5 \text{ driving} \times 5
\text{ scoring} \times 25 \text{ seeds} \times 6 \text{ windows} =
7{,}500$ rows.

## 5. Fleet-state evolution

At each window, the \textit{driving method} for the run selects the top-$K$
pairs. Those pairs are remediated, new CVEs disclosed, EPSS random-walked,
and telemetry updated --- identical mechanics to Paper~5's
\texttt{advance\_window}. The \textit{scoring methods} are evaluated on the
state \textit{before} that window's evolution and recorded; their selections
have no effect on the trajectory.

## 6. Metrics

- **P@50** per (cell, driver, scorer, seed, window).
- **Per-pair dominance fraction**: $\Pr[\mathrm{P@50}^{\mathrm{HP}} > \mathrm{P@50}^{\mathrm{m}}]$
  per (cell, driver) over the 150 seed-window pairs.

## 7. Statistical reporting

95\% percentile bootstrap CIs (10{,}000 resamples). No NHST. All
claims trace to `paper9/results/primary_v1/self_traj_results.csv`.

## 8. Reproducibility

From `paper9/`:
```
PYTHONPATH=src python3 src/run_self_traj.py
```
Reuses Paper 4/5 code via sys.path injection.

## 9. Out of scope

- Sweeping $\lambda$ or extending the K grid — held to canonical points
  for tractability.
- Online recalibration: this paper uses fixed Paper~4 weights to isolate
  the trajectory question (consistent with the Paper~7 + Paper~8
  finding that fixed weights are the operationally correct baseline at
  high capacity).
- Cross-trajectory rank stability beyond P@50 — future work.

## 10. Author certification

Cell grid, methods, hypotheses, decision rules, and stop rules above
were fixed before any self-trajectory result was computed.

Signed: Harshavardhan Malla, 2026-06-05.
