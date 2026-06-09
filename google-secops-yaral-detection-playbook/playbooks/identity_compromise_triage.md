# Identity Compromise Triage Playbook

**Owner:** Harshavardhan Malla
**Related detections:** I1 (impossible travel), I2 (brute force → success), I3 (password spray), I4 (MFA fatigue), I5 (rapid user create/delete), P1 (privileged group change)

## Escalation criteria
Escalate to High when the alert includes any of:
- failures-then-success sequence on the same account
- impossible travel across two cities/countries inside one hour
- MFA fatigue (many prompts ending in approval)
- new-device or new-user-agent sign-in for a privileged user
- risky / hostile source IP
- post-login privilege changes (group adds, role assignments, app consents)

## Investigation steps
1. Build the authentication timeline: failures, successes, MFA challenges, conditional-access decisions.
2. Compare source IPs, geolocation, devices, user agents.
3. Check MFA method and outcome.
4. Review recent password-reset / helpdesk activity.
5. Review mailbox rules, OAuth grants, VPN connections, cloud console access.
6. Identify whether sensitive systems or data were touched after login.
7. Hunt for other users impacted from the same source IP / ASN.

## Response actions
- Revoke active sessions.
- Reset password.
- Re-register MFA.
- Temporarily disable the account if compromise is confirmed.
- Block the source IP / ASN.
- Audit for persistence (inbox rules, OAuth apps, forwarding, delegated mailboxes, IAM grants).
- Notify the user and management out-of-band (phone, in-person) — not via the compromised channel.
