# Paper 7 — Pre-Registration Protocol

**Working title:** Rolling-History Online Calibration for Hygiene-Augmented
Vulnerability Prioritization: Closing the Fixed-Weight Gap Without
Future-Data Leakage

**Authors:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**Date locked:** 2026-06-04 (before any online-calibration result was inspected)
**Builds on:** Paper 4 (HygienePrio scorer + EEHDA generator), Paper 5
(multi-window simulator + offline recalibration ablation), Paper 6
(capacity-arrival sweep + W6 collapse finding at high K).

---

## 1. Motivation

Paper 5's H3 ablation showed that grid-searching scorer weights at each
window on the calibration seeds' *current-window* state and applying the
fitted weights to the evaluation seeds at the *same* window adds up to
$+21.3$ pp at W2 over Paper 4's fixed weights. That ablation uses
\textit{future-window} state for calibration: at the moment a real operations
team has to choose weights for window $w$, they have not yet observed
window-$w$ data. Paper 5's H3 result is therefore an offline ceiling, not
a deployable procedure.

Paper 6 documented a parallel finding: at high capacity ($K \in \{100, 200\}$),
HygienePrio-full's absolute W6 P@50 collapses alongside EPSS-only, with
the worst cell ($K=200, \lambda=1$) producing $0.062$. A natural question
is whether \textit{rolling-history online calibration} ---refitting weights
each window using only past windows of the calibration seeds---
recovers any portion of the offline-peek gain, and in particular whether
it rescues HygienePrio at the high-capacity cells.

## 2. Research questions

- **RQ1.** Does rolling-history online calibration beat the fixed Paper~4
  weights at every window?
- **RQ2.** Does rolling-history online calibration approach the offline-peek
  ceiling (Paper~5 H3)?
- **RQ3.** Does online calibration rescue HygienePrio-full at the
  high-capacity cells where Paper~6 reported collapse?

## 3. Calibration strategies (locked)

Three strategies are compared at every (cell, window):

| Tag | Strategy | At window $w$, calibration data = ... |
|-----|----------|----------------------------------------|
| `fixed` | Paper~4 weights, never refit | none |
| `online` | Rolling-history grid search | calibration seeds at window $w-1$ only |
| `offline` | Paper~5 H3 peek calibration | calibration seeds at window $w$ |

At W1, both `online` and `offline` reduce to `fixed` because no history
is available. From W2 onward they diverge: `online` uses the *previous*
window's calibration-seed state (no leakage), `offline` uses the *current*
window's calibration-seed state (peeks at the window it is scoring).

The grid is identical to Paper~5 §H3:
$\alpha \in \{0.5, 0.7, 0.9\}$, $\beta \in \{0.3, 0.5, 0.7\}$,
$\gamma \in \{0.0, 0.1, 0.2\}$, $\delta \in \{0.0, 0.1, 0.2, 0.3\}$
(108 grid points).

## 4. Hypotheses

| ID | Statement | Decision rule |
|----|-----------|---------------|
| H1 | Online $\geq$ fixed at every window, every cell. | Supported if all (cell, window) $\Delta_{\text{online}-\text{fixed}} \geq -0.01$ (i.e. online never loses by more than 1 pp). |
| H2 | Online $\leq$ offline at every window. | Supported if all (cell, window) $\Delta_{\text{online}-\text{offline}} \leq +0.01$. |
| H3 | At high-capacity cells ($K \in \{100, 200\}$), online recovers $\geq 5$ pp of the offline-fixed gap at W4 or later. | Supported if for at least one $w \in \{4,5,6\}$ and one $K \in \{100, 200\}$, $(\text{online} - \text{fixed}) \geq 0.5 \cdot (\text{offline} - \text{fixed})$ and absolute online gain $\geq 0.05$. |

**Stop rules:**
- If H1 is rejected on more than three cell-window pairs, the abstract is
  rewritten to qualify the deployability claim before any operational
  recommendation is drafted.
- If H3 is rejected, the rescue claim is dropped and the paper reports
  the negative result as the headline contribution.

## 5. Cell grid

Three capacity levels at the Paper~6-canonical arrival rate:
$K \in \{50, 100, 200\}$, $\lambda = 3$. Three cells x six windows x
three calibration strategies x 25 evaluation seeds. Total rows: $1{,}350$
(rows are per-seed per-cell per-window per-strategy).

The high-capacity cells ($K = 100, 200$) are exactly Paper~6's H4-rejected
collapse cells; the low-capacity cell ($K = 50$) anchors against Paper~5's
canonical setting.

## 6. Metrics

- **P@50** per (cell, seed, window, strategy), primary.
- **Online recovery ratio**:
  $(\text{online}_{w} - \text{fixed}_{w}) / (\text{offline}_{w} - \text{fixed}_{w})$
  reported per (cell, window) when $(\text{offline} - \text{fixed}) > 0.01$.

## 7. Statistical reporting

- 95\% percentile bootstrap CIs with 10{,}000 resamples for cell-mean
  point estimates~\cite{efron1994introduction}.
- No null-hypothesis significance tests.
- All numerical claims trace to `paper7/results/primary_v1/online_calib_results.csv`.

## 8. Reproducibility

The runner is `paper7/src/run_online_calib.py`. From `paper7/`:
```
PYTHONPATH=src python3 src/run_online_calib.py
```
The runner reuses Paper 5's window simulator and Paper 4's scorer
package via `sys.path` injection.

## 9. Out of scope

- Online learning approaches other than grid-search-on-rolling-history
  (gradient-based, Bayesian, contextual bandits) are excluded.
- Real fleet data: not used. All claims bounded to synthetic.
- Sweeping $\lambda$: held at 3 to keep scope tractable; $\lambda$
  sensitivity is a follow-up.

## 10. Author certification

I certify that the cell grid, calibration strategies, hypotheses,
decision rules, and stop rules above were fixed before any online-calibration
result was computed. Any deviation discovered during execution will be
reported in a "Pre-registration deviations" subsection of the manuscript.

Signed: Harshavardhan Malla, 2026-06-04.
