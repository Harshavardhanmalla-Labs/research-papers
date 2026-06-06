# Paper 7 Supplementary Experiments

The directories under `paper7/experiments/` contain experimental
artifacts (protocols, code, frozen CSVs) for **extension experiments
that are NOT part of Paper 7's primary submission**. They are
preserved here for reproducibility and to support potential
follow-up papers.

These experiments were generated during exploratory `/loop` runs
on 2026-06-04 and 2026-06-05 as natural next-steps motivated by
Paper 7's K=200 hazard finding. They were not in the original
9-topic research plan and are not currently planned as standalone
submissions.

## Directory map

| Sub-directory | Question explored | Frozen rows |
|---|---|---|
| `03_adaptive_single_tau/` | Does a one-threshold magnitude detector ($\tau = 0.05$) avoid the K=200 hazard? | 2,250 |
| `04_tau_sweep/` | Does any $\tau \in \{0.02, \ldots, 0.10\}$ reach the H1/H2 joint feasibility region? | 11,250 |
| `05_capacity_aware/` | Does a per-K threshold vector $\tau_K$ reach feasibility? | 2,700 |
| `06_cusum/` | Does one-sided CUSUM ($k=0.04, h=0.10$) beat the static gate at K=200? | 2,700 |

## Status

Each sub-directory contains its own `design/PROTOCOL.md`,
`src/`, `results/`, and `submission/ieee/` artifacts from when they
were initially built as separate manuscripts. The `submission/ieee/`
PDFs compile but are **not part of the 9-topic research program**.

If any of these directions becomes a planned primary submission,
the appropriate next step is to promote it to a top-level paper
directory and re-evaluate its pre-registration discipline
(particularly: were the parameters truly locked before evaluation,
or did the loop-driven generation compromise the pre-registration?).
