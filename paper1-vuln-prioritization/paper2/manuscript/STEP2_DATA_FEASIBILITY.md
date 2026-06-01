<!--
Paper 2 — Step 2: Public-Feed Data Feasibility & Calibration Readiness.
Internal planning document. No fabricated data ([VERIFY] for unconfirmed facts).
Paper 1 (../paper/, results/primary_full_v1/) is NOT touched by this work.
-->

# Paper 2 — Step 2: Public-Feed Data Feasibility & Calibration Readiness

**Method:** repo inspection only (no fetches, no experiments, Paper 1 untouched).
Exact CVE/KEV counts require an actual fetch and are marked `[VERIFY]`.

**Decision: CONDITIONAL GO** — public-feed calibration is *plausibly* feasible but
**not proven**; it hinges on the distinct-positive-CVE count, which only a fetch
(Step 3 probe) can confirm. Feasibility score **6/10**.

## 1. EPSS historical data
- Daily snapshots from **2021-04-14** (`EPSS_HISTORY_BEGIN`), FIRST API +
  `epss_scores-YYYY-MM-DD.csv.gz` mirror; as-of supported.
- Coded model boundaries: v1 2021-04-14, v2 2022-02-04, **v3 2023-03-07, v4
  2025-03-17**. Scores are **not comparable across versions** → restrict
  calibration to a single era. **v3 era (2023-03-07 → 2025-03-16, ~24 months)** is
  the longest clean window.
- License `[VERIFY]` (EPSS generally free). Excellent for the E feature/baseline;
  must wire EPSS-as-of-t0 into features (new work).

## 2. CISA KEV catalog
- Cumulative; `dateAdded`/`dueDate`; as-of reconstruction (`dateAdded <= d`).
- **CISA/US-gov public domain → redistributable.** Supports Label A + K feature.
- **Central limitation:** KEV is rare → **Label A positives scarce** after
  catalog matching (the binding feasibility constraint).

## 3. Public PoC / ExploitDB
- `poc_client` is **license-gated** (redistribution unresolved); local CSV
  normalization works. **Label B computable locally but NOT redistributable** →
  local-only robustness axis; PoC labels/features must not ship. Noisy/biased.

## 4. NVD / CVE / CVSS
- `extract_cvss` (v4/v3.1), `extract_cpe_matches`, `parse_cpe23`,
  `normalize_nvd_record`, `fetch_nvd_window`. Published dates available.
- Limitations: CPE applicability noisy/incomplete `[VERIFY]`; v4 coverage partial
  for older CVEs (v3.1 dominant in the v3-EPSS era).

## 5. Synthetic fleet generator
- **31 real high-CVE-volume products** in the catalog (Chrome, OpenSSL, OpenSSH,
  log4j, nginx, httpd, Tomcat, Postgres, MySQL, MSSQL, Java, Python, .NET, …) —
  far better than the 5-CVE toy set.
- **Scale-up needed:** experiments are wired to the toy fixture; no public-CVE
  ingestion + CPE→catalog mapping yet. Pairs will be plentiful, but **effective
  calibration N ≈ distinct labeled CVEs** (pairs sharing a CVE share its label),
  which KEV rarity caps.

## 6. Existing code readiness
Built: feed clients, snapshot cache + fetch scripts, Label A/B + no-future-leakage,
calibration (logistic/ridge, time-block CV, neg-coef clip, bootstrap CI), GBT
comparator, metrics + paired stats, controlled-run + freeze/verify + inspector.
Missing: real cached data; public-CVE ingestion + CPE mapping; real EPSS/KEV-as-of-t0
feature wiring; multi-t0 calibration-set assembly + CVE-level dedup + imbalance
handling.

## 7. Minimum viable calibration dataset
Single EPSS era (v3 recommended); 31-product catalog (optionally expand to ~50);
target ≥ ~2,000–5,000 matched distinct CVEs `[VERIFY]`; positives ~1–5% → order
50–250 positive CVEs in train `[VERIFY]` (make-or-break); monthly t0 (12–18 dates);
30 seeds; features E/K/S real + C/X/R/U synthetic; Label A primary (KEV-only
redistributable), Label B local-only; temporal train/gap/test; **calibrate at
distinct-CVE level**.

## 8. Calibration feasibility risks (summary)
Too few positives (High); class imbalance (High); Label B noisy + non-redistributable
(Med-High); EPSS leakage (Med); weak CPE matching (Med); small catalog (Med);
overfitting synthetic artifacts (High); result still neutral (High, not a kill);
licensing (Med). Kill/pivot: <~20 positive CVEs → pivot away from calibration.

## 9. Feasibility smoke test
Fetch a small real window (KEV/NVD/EPSS public; PoC gated/skipped), match CVEs to
catalog, build a small fleet + pairs at t0, attach real EPSS/KEV as-of t0, compute
Label A over (t0, t0+H], count distinct/positive CVEs, attempt minimal calibration
only if positives ≥ threshold. Success: ≥ ~50 positive CVEs + non-degenerate
weights. (Implemented in Step 3 as `scripts/paper2_feasibility_probe.py`.)

## 10. Decision
**CONDITIONAL GO.** Run the feasibility probe FIRST (the real gate for condition #2).
Do not proceed to pre-registration/full calibration until it confirms ≥ ~50 positive
CVEs and non-degenerate weights. If it fails → PIVOT to a robustness/sensitivity
study without calibration. Effort: moderate (ingestion/mapping glue + configs;
calibration/labels/stats already built).
