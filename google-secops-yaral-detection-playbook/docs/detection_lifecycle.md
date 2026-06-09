# Detection Lifecycle

1. **Hypothesis** — one honest sentence describing the attacker behavior.
2. **Telemetry validation** — confirm required UDM fields are populated. Use the SecOps UDM Lookup tool.
3. **Draft** — write the rule. Decide single-event vs multi-event deliberately.
4. **Historical testing** — run against 7 / 14 / 30 days of history. Bucket matches by host, user, command line.
5. **Tuning** — add reference-list exclusions backed by evidence. Set severity and risk score.
6. **Production** — promote only when it compiles, volume is manageable, triage is clear, response is defined.
7. **Continuous improvement** — re-review after FP spikes, incidents, intel changes, parser changes, log-source changes, business-process changes, new attacker techniques.
