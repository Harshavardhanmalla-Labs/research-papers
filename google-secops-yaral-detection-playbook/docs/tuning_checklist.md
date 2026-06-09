# Rule Tuning Checklist

Before promoting any rule to production, every box must be ticked.

- [ ] Rule compiles in the SecOps Rules Editor.
- [ ] All referenced UDM fields are populated in your logs.
- [ ] Historical test run over 7, 14, and 30 days.
- [ ] Alert volume reviewed and acceptable.
- [ ] Top false-positive sources identified.
- [ ] Admin / automation / scanner exclusions added via reference lists (not hard-coded).
- [ ] Service-account exclusions justified case-by-case.
- [ ] Severity and risk score match business risk.
- [ ] Triage steps are concrete and actionable.
- [ ] Detection output carries useful context (`outcome` variables).
- [ ] Mapped to MITRE ATT&CK.
- [ ] Owner assigned and review cadence set.
- [ ] Expected response action documented.
