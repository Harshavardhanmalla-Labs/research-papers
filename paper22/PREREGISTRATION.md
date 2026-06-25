# ENSES — Pre-registration & honest-data statement

**Paper (working title):** An Explainable Neuro-Symbolic Expert System for
Autonomous Cyber-Risk Prioritization in Smart-City and IIoT Infrastructure.
**Target venue:** Expert Systems with Applications (ESWA).
**Frozen results:** `results/primary_v1/` (`primary_summary.json`, `methods.csv`).

## Data (no fabrication)

- **Real, public:** FIRST.org EPSS + CISA KEV snapshot (2026-06-05), 203,174 CVEs
  (>= 2020); 1,612 known-exploited with real CWE, description, vendor/product, and
  ransomware-use metadata. Re-fetchable; in `real_data/`.
- **Transparent synthetic estate:** a smart-city / IIoT / connected-healthcare
  asset estate (6 asset classes, criticality tiers) generated from documented
  distributions; differential-privacy (Laplace) noise applied to *released*
  aggregate statistics. We do **not** claim real corporate logs.
- **Ground-truth harm** of an (asset, CVE) pair = exploited(KEV) x
  criticality-weight x latent applicability, where applicability is a noisy blend
  of product-metadata match, CWE-class affinity, and description semantics plus
  irreducible noise — so no tier or model perfectly recovers it.

## System (ENSES)

- **Symbolic tier (knowledge graph + rules):** CVE -> CWE -> weakness-class ->
  ATT&CK-tactic -> asset-class; product/vendor -> asset-class applicability;
  exploitation/ransomware escalation rules.
- **Neural tier (RAG):** `nomic-embed-text` embeddings of real CVE descriptions vs
  asset-class profiles (semantic relevance).
- **Inference engine:** a learned, additive **glass-box** fusion over interpretable
  features {EPSS, KEV, ransomware, criticality, metadata-relevance, KG-relevance,
  neural-relevance} plus the domain interaction *exploitability x criticality x
  relevance* (the canonical risk equation). Each decision = sum of named
  contributions -> inherently explainable.

## Pre-registered hypotheses (all supported; BCa 95% CIs, 25 seeds)

- **H1.** ENSES > EPSS-only on harm-weighted Precision@100. Supported: delta
  +0.663, CI [0.654, 0.674].
- **H2.** ENSES is at least as good as a black-box gradient-boosted ensemble on the
  same signals while remaining explainable. Supported: delta +0.014, CI
  [0.008, 0.020]; ENSES also ~5x lower inference latency.
- **H3.** Each neuro-symbolic tier is necessary: ablating the neural tier, the
  knowledge-graph tier, or the asset-criticality tier each reduces performance
  (−0.07, −0.04, −0.47 at wp@100 respectively).

## Metrics

Harm-weighted Precision@k (k in {50,100,250,500}), NDCG@100, inference latency
(microseconds per pair). Baselines: EPSS-only, KEV-first, random, and the
gradient-boosted ensemble. Reproduce: `python src/run_eval.py` (embeddings cached).
