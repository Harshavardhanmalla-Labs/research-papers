# Paper 10 — Pre-Registration Protocol

**Working title:** AutoHeal — A Self-Healing Framework for Autonomous
Vulnerability Remediation: A Pre-Registered Evaluation on the EEHDA
Synthetic Fleet with Real CVE Telemetry

**Author:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**Date locked:** 2026-06-05 (before any AutoHeal evaluation-seed result was inspected)
**Builds on (synthesis paper):** Paper 3 (HygieneBench), Paper 4 (HygienePrio),
Paper 5 (Temporal Stability), Paper 6 (Capacity-Indexed Decay), Paper 7
(Lag-1 Online Calibration), Paper 8 (Multi-History Smoothing), Paper 9
(Self-Trajectory + Theorem 1), and the real CVE/EPSS/KEV corpus from
`real_data/processed/`.

---

## 1. Motivation

Papers 3–9 of the VulnPrio sequence established a coherent picture of
hygiene-augmented vulnerability prioritization in synthetic and partial
real-distribution settings. The findings are scoring-recommendation-level
results: "use HygienePrio for ranking" (Paper 4), "expect capacity-driven
collapse at high K" (Paper 6), "deploy lag-1 calibration below K=100"
(Paper 7), "decouple scoring from selection at high K" (Paper 9), and
"the +31 pp synthetic gap shrinks to +2.4 pp under real distributions"
(Paper 4 §12).

None of these papers addresses the operational question that motivated
the program in the first place: \emph{can a closed-loop framework actually
perform autonomous remediation under safety bounds?} The components are
all available (scoring rule, calibration recipe, capacity model, theorem
on signal exhaustion). What has not been built is the integrating
architecture that combines them and produces an operationally
deployable system.

AutoHeal is that framework. The paper is a synthesis paper: it builds
the architecture from the program's accumulated findings, locks the
safety-bound hypotheses before evaluation, and reports honestly on
where autonomous remediation works and where it cannot safely operate.

## 2. Research questions

- **RQ1.** Can an autonomous self-healing framework, configured with
  Papers 4–9's findings, remediate $\geq 80\%$ of high-priority
  CVEs within 14 days of disclosure?
- **RQ2.** Can it operate at a safety bound of $\leq 5\%$ rollback rate
  on remediation actions?
- **RQ3.** Does it reduce mean-time-to-remediation (MTTR) for KEV-listed
  CVEs by $\geq 50\%$ vs.\ a human-in-loop baseline?
- **RQ4.** Does it preserve Paper 4's per-pair dominance of
  HygienePrio over EPSS-only in $\geq 80\%$ of evaluation pairs at the
  scale of a real-world fleet simulation?

## 3. AutoHeal architecture (locked before evaluation)

AutoHeal is a six-stage pipeline. Stages run per maintenance window:

```
[detect] -> [score] -> [triage] -> [plan] -> [act] -> [verify+rollback] -> [learn]
```

Each stage's parameters are pre-registered.

### Stage 1: Detect
Scan the EEHDA fleet's `vulnerability_records` table; identify all
(host, CVE) pairs where `patched=False`. Use the real EPSS/KEV corpus
(from `real_data/processed/`) for CVE attribute lookup.

### Stage 2: Score
Apply Paper 4 HygienePrio scorer with calibrated weights
$(\alpha, \beta, \gamma, \delta) = (0.7, 0.5, 0.1, 0.2)$. At each
window, apply Paper 7 lag-1 calibration **only** if cell capacity
$K \leq 100$; otherwise hold fixed Paper 4 weights (Paper 7's
deployable recipe).

### Stage 3: Triage (3 classes, pre-registered thresholds)

For each (host, CVE) pair, classify into:

- **AUTO** (auto-remediate):
  HygienePrio score $\geq 0.8$ AND host criticality $\neq$ CRITICAL
  AND known-blocking-config absent AND patch-test-suite present.
- **REVIEW** (human-in-loop):
  HygienePrio score $\in [0.5, 0.8)$, OR host criticality = CRITICAL,
  OR known business-hours constraint.
- **DEFER**:
  HygienePrio score $< 0.5$ OR known-incompatible patch.

### Stage 4: Plan (capacity-constrained scheduling)

Select top-$K$ pairs from the AUTO bucket subject to per-window
capacity $K$ (pre-registered $K = 50$ for moderate-fleet scenario,
exercising Paper 7's recommended regime). Higher-priority pairs scheduled
first.

### Stage 5: Act (simulated patch operation)

For each scheduled pair, simulate the patch operation with a
pre-registered failure-mode distribution drawn from public sysadmin
literature:
- Success: 92%
- Rollback (post-patch health-check failure): 5%
- Defer (patch blocked, no action taken): 3%

### Stage 6: Verify + Rollback (safety mechanism)

For each AUTO-acted pair, run post-action health check (simulated as
deterministic from the seed). On health-check failure: rollback the
patch and re-classify as REVIEW for the next window. Track rollback
rate per window and per cell.

### Stage 7: Learn (Paper 7 online calibration)

If cell $K \leq 100$, re-run lag-1 calibration on the rollback
outcomes. Update weights for next window.

### Pre-registered safety bounds (hard stops):
- **Rollback rate > 10% at any window:** halt AutoHeal, fall back to
  human-in-loop.
- **Cascading-failure detection** (more than 5 rollbacks share a
  common patch ancestor): halt, escalate to human.

## 4. Cell grid (locked)

The evaluation runs on:
- Capacity $K \in \{50, 100, 200\}$ (matching Papers 6/7 grid)
- Arrival rate $\lambda = 3$ (Paper 5 canonical)
- Windows $W = 12$ (28 days of bi-weekly cycles; 2x Paper 5's window count)
- 25 evaluation seeds (105–129; matching all prior papers)
- 3 strategies: AutoHeal, Human-in-loop baseline, Fixed-policy baseline

Total: $3 \times 12 \times 25 = 900$ window-seed rows per strategy;
$2{,}700$ total.

## 5. Baselines

- **Human-in-loop**: classify all pairs as REVIEW; remediate at fixed
  $K = 30$/window (typical human triage capacity per Verizon 2026 DBIR
  $\sim$43-day MTTR baseline).
- **Fixed-policy**: classify by Paper 4 fixed weights only; no
  recalibration; same $K$ as AutoHeal.

## 6. Pre-registered hypotheses

| ID | Statement | Decision rule |
|----|-----------|---------------|
| H1 | Coverage: AutoHeal remediates $\geq 80\%$ of EPSS $> 0.5$ CVEs within 14 days (W$\leq 6$). | Supported if cell-mean coverage $\geq 0.80$ at $K = 50$ and $K = 100$. (K=200 excluded by Paper 9 Corollary 4.) |
| H2 | Safety: rollback rate $\leq 5\%$ at every (cell, window). | Supported if no (cell, window) exceeds the threshold. |
| H3 | MTTR reduction: AutoHeal MTTR $\leq 50\%$ of Human-in-loop MTTR for KEV-listed pairs at K $\in \{50, 100\}$. | Supported if cell-mean ratio $\leq 0.5$. |
| H4 | Per-pair dominance: AutoHeal beats Human-in-loop on Precision@50 in $\geq 80\%$ of (cell, seed, window) triples at K $\leq 100$. | Supported if dominance fraction $\geq 0.80$. |

**Stop rules:**
- If H2 is rejected, the abstract leads with the safety-violation finding
  and AutoHeal is reported as not deployable in the affected regimes.
- If H1 OR H3 is rejected, the recommendation table in the discussion
  is rewritten to qualify the auto-remediation regime accordingly.

## 7. Reporting

- 95% percentile bootstrap CIs (10,000 resamples)
- No NHST
- All claims trace to `paper10/results/primary_v1/autoheal_results.csv`
- All numerical figures verifiable from the frozen run

## 8. Reproducibility

From `paper10/`:
```
PYTHONPATH=src python3 src/run_autoheal.py        # 2,700-row eval
PYTHONPATH=src python3 src/analyze.py             # H1-H4 outcomes
PYTHONPATH=src python3 src/make_figures.py        # 3 figures
```

Re-uses Papers 4 and 5's packages via sys.path; consumes
`real_data/processed/cve_corpus_for_sampling.csv` for real CVE
attributes; deterministic from seed list.

## 9. Out of scope

- Real fleet deployment (no real fleet available).
- Multi-tenant attacker model beyond Paper 4 §13's Stackelberg
  single-shot game.
- Reinforcement-learning policy updates (Paper 9 future work).
- Network-layer or supply-chain remediation; AutoHeal is bounded to
  host-level patch operations.

## 10. Certification

I certify that the AutoHeal architecture, triage thresholds, safety
bounds, capacity parameters, hypotheses H1–H4, decision rules, and
stop rules above were fixed before any evaluation-seed AutoHeal
result was computed.

Signed: Harshavardhan Malla, 2026-06-05.
