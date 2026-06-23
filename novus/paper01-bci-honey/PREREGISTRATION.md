# Pre-registration — BCI-Honey (Paper 1)

Frozen **before** inspecting any test-set result. Authored: NovusAI honeypot track.

## Data
- **Source:** CyberLab honeynet dataset, Zenodo DOI 10.5281/zenodo.3687527 (CC BY 4.0),
  Sedlar, Kren, Stefanič Južnič, Volk (2020). Real Cowrie SSH/Telnet honeypots, ~50 nodes.
- **Sample:** 10 daily captures spanning 2019-05 → 2020-02 (one per month), 16 sensors.
- **Unit:** one attack session. N = 378,999 real sessions after parsing.

## Intent taxonomy (observed, ATT&CK-aligned; dominant-class priority, disclosed)
Derived from the FULL session via observed events, priority order:
1. `malware_delivery` — any `file_download` (T1105 Ingress Tool Transfer) — 0.6%
2. `tunneling` — any `direct-tcpip` and no download (T1090 Proxy / relay abuse) — 6.4%
3. `execution` — any command event and no tunnel/download (T1059) — 0.2%
4. `bruteforce` — login/connect only (T1110) — 92.8%

## Tasks
- **Task A — Engagement (binary):** y = (intent ≠ bruteforce). Base rate ≈ 7.2%.
  Operational use: flag sessions likely to escalate so the honeypot can adapt deception early.
- **Task B — Intent typing (4-class):** predict the dominant intent class.

## Model inputs — EARLY-PHASE features only (no action-phase leakage)
Connection + client-fingerprint + authentication signals, all structurally prior to any
command/tunnel/download:
`proto, ssh_ver (top-K + other), n_enc, n_kex, n_mac, n_key, has_hassh, n_auth, n_auth_ok,
n_distinct_creds, max_pw_len, empty_pw, common_user, hour`.
**Excluded as leaky** (defined via the action boundary): `time_to_action`, `n_early_events`,
and all action-phase counts (`n_cmd*`, `n_tcpip`, `tunnel_port`, `n_download`, `duration`).

## Models & baselines
- **BCI model:** Random Forest + gradient-boosted trees (class-weighted for imbalance).
- **Baselines:** prior-rate / majority, protocol-only, single-strongest-feature (n_auth).

## Validation
- **Temporal split:** train 2019-05…2019-11, test 2019-12…2020-02 (predict future from past;
  the months exhibit real drift, 1.5%→12.8% engagement).
- Metric per task: Task A — PR-AUC (primary; imbalance-appropriate), ROC-AUC, Precision@1% and
  @5% with lift; Task B — macro-F1, balanced accuracy, per-class F1.
- **Uncertainty:** BCa bootstrap (10,000 resamples) over test sessions; paired deltas vs baselines.

## Pre-registered hypotheses (each supported iff its BCa 95% CI excludes zero in the stated direction)
- **H1:** BCI PR-AUC (Task A) > prior-rate baseline PR-AUC.
- **H2:** BCI Precision@1% > base engagement rate (lift > 1) — early flagging beats chance.
- **H3:** BCI macro-F1 (Task B) > protocol-only baseline macro-F1.
- **H4 (robustness):** H1 holds on the held-out FUTURE test months (temporal generalization),
  not only under random CV.

Outputs frozen to `results/primary_v1/`. No hypothesis or feature set changes after this point;
if the method underperforms we improve the method (features/model), never the labels or split.
