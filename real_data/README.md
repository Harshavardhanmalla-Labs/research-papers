# real_data/ — Public CVE/EPSS/KEV Snapshot + Validation

Snapshot of FIRST.org EPSS scores + CISA KEV catalog (2026-06-05) used
for partial external-validity evaluation of Papers 4 and 9.

This is **public-feed data only** — no private fleet telemetry, no
proprietary data. All sources are free and re-fetchable.

## Sources

| Source | URL | Snapshot |
|---|---|---|
| EPSS | `epss_scores-current.csv.gz` | 338,274 CVEs (2026-06-05) |
| KEV  | `known_exploited_vulnerabilities.json` | 1,612 entries (2026-06-05) |

## Files

```
real_data/
├── raw/
│   ├── epss.csv.gz            # FIRST.org EPSS snapshot
│   ├── epss.csv               # uncompressed
│   └── kev.json               # CISA KEV catalog
├── processed/
│   ├── cve_corpus_2020plus.csv          # 203,174 CVEs >= 2020
│   ├── cve_corpus_for_sampling.csv      # same; for evaluation sampling
│   └── manifest.json                    # snapshot metadata + distribution stats
├── results/
│   ├── real_dist_results.csv            # Paper 4 external-validity eval
│   ├── comparison_summary.json          # synthetic vs real
│   └── adversarial_results.csv          # Paper 4 adversarial eval (450 rows)
├── real_dist_evaluator.py               # external-validity runner
└── adversarial_eval.py                  # adversarial Stackelberg simulator
```

## Headline finding

The HygienePrio Precision@50 advantage over EPSS-only shrinks from
**+30.9 pp** under synthetic CVE attributes to **+2.4 pp** under real
EPSS distributions. The qualitative ordering is preserved; the
quantitative magnitude is not robust to attribute-distribution shift.

## Adversarial finding

Under a Stackelberg attacker who games 5% of low-HRS pairs, HygienePrio
degrades by only −1.4 pp while EPSS-only degrades by −13.6 pp. The
HP−EPSS gap **widens** from +26.4 pp to +38.6 pp under attack.

## Reproduce

```bash
python3 real_data/real_dist_evaluator.py
python3 real_data/adversarial_eval.py
```

Both runners deterministic from seed list (105–129 from Paper 4).
