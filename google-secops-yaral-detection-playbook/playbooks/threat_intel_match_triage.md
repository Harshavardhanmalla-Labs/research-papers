# Threat-Intel Match Triage Playbook

**Owner:** Harshavardhan Malla
**Related detections:** P2 (outbound to watchlist IP) and any IOC/reputation-style rules.

## Investigation steps
1. Confirm the match source and confidence (which feed, which campaign, last seen).
2. Identify source host, user, process initiating the connection.
3. Assess destination reputation, associated malware families, hosting provider.
4. Determine whether the connection was allowed or blocked at the perimeter.
5. Pivot to DNS, proxy, firewall, EDR, and SIEM telemetry for context.
6. Find other hosts touching the same indicator.
7. Rule out benign explanations: shared hosting, CDN, sinkhole, security scanner.
8. Escalate if confirmed C2 or malware infrastructure.

## Response actions
- Block the indicator at the firewall, proxy, DNS, and EDR.
- Isolate the endpoint if behavior looks like live C2.
- Run an enterprise-wide exposure search for the indicator.
- Push the indicator to internal watchlists.
- Strengthen the rule's context (add the host's recent processes / parent chain to `outcome`).
- Document the outcome (TP / FP / inconclusive) for detection-health metrics.
