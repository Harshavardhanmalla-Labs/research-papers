# Self-Trajectory Evaluation of Hygiene-Augmented Vulnerability Prioritization

**Authors:** Harshavardhan Malla, Independent Researcher
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**Date:** June 2026
**Status:** Draft v0.1

---

## Abstract

Papers 5–8 of the VulnPrio sequence all share an evaluation convention: HygienePrio-full under fixed weights drives the fleet trajectory for every method scored at every window. This choice is methodologically necessary for cross-method identifiability but introduces an unmeasured bias — each method is scored against a backlog its own weights did not produce. This paper quantifies that bias by re-running every method on its OWN fleet trajectory and reporting how the previous papers' headline findings change.

We ran a pre-registered 7,500-row evaluation at K ∈ {50, 200}, λ = 3, six windows, 25 evaluation seeds, with each of five scoring methods driving its own fleet evolution. **All three pre-registered hypotheses are rejected, and the rejection pattern retroactively reframes Papers 5–8.**

**First**, Paper 6's headline "HygienePrio collapses at high capacity" finding is *rejected as an intrinsic property of hygiene-augmented scoring*. At K = 200, W6, HygienePrio-full's mean P@50 is 0.075 on its own trajectory but 0.701 on CVSS-driven, 0.713 on HRS-driven, and 0.706 on Random-driven trajectories. The collapse is a recursive-deployment artefact: HygienePrio's own selection preferentially drains the HRS upper tail that HygienePrio's score depends on.

**Second**, EPSS-only's selection at K = 200 produces a literal zero W6 P@50 for every scorer (range 0.001–0.012). The ground-truth positive set is structurally exhausted by EPSS-only's aggressive remediation of the high-EPSS tail. EPSS-self-driven at high capacity is the deepest sink in the studied grid.

**Third**, HygienePrio's per-pair dominance over EPSS-only is trajectory-conditional. At K = 50 it is 1.000 under every driver; at K = 200 it is 1.000 under HRS, CVSS, and Random drivers, 0.800 under HP's own driver, and 0.393 under EPSS-only's driver (where both methods collapse together). Paper 5's 96% headline statistic is preserved at moderate capacity and under HRS-blind drivers.

We additionally prove a **Closed-Loop Signal Exhaustion Theorem** (§12) that formalises the empirical finding: any deterministic scoring policy whose top-K selection is positively correlated with its own discriminative signal converges to the random baseline in finite windows under capacity-constrained closed-loop deployment. Four corollaries cover the randomised, ε-greedy, high-arrival, and online-recalibrated extensions.

The operational reading is sharper than Papers 5–8 allowed: HygienePrio is a strict improvement over EPSS-only across the studied regimes whenever the deploying organisation does not let HygienePrio also drive the patching queue at high capacity. The Paper 6 H4 collapse is a known closed-loop hazard, not a property of the scoring method itself, and is operationally controllable by decoupling scoring from selection.

**Keywords:** vulnerability prioritization; selection policy; counterfactual trajectory; closed-loop bias; signal exhaustion theorem; HygienePrio; pre-registration; reproducibility.

---

The full submission manuscript is at `submission/ieee/main.tex` (compiles to 10 pages via tectonic).
The pre-registration protocol is at `design/PAPER9_PROTOCOL.md`.
Frozen results: `results/primary_v1/self_traj_results.csv` (7,500 rows).
