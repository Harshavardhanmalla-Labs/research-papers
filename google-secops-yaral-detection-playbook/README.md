# Google Security Operations — YARA-L Detection Engineering Playbook
**Author:** Harshavardhan Malla
**Discipline:** Threat Detection Engineering · Google Security Operations (SecOps) · YARA-L 2.0 · UDM · MITRE ATT&CK · MDR Operations · Incident Response Automation
**Status:** Portfolio-grade reference. Validate every rule in your own tenant before production.

---

## Why this playbook exists

Most "detection libraries" are just piles of alert logic. Someone pasted a regex, gave it a scary name, and shipped it. Six weeks later the SOC has 4,000 alerts a day, nobody trusts any of them, and the rule that would have caught the real intrusion is buried under noise that nobody had the time to tune.

This playbook is the opposite of that. It is built around one belief I keep coming back to in real operations:

> **A detection is not finished when it fires. It is finished when an analyst can act on it.**

So every rule in here is treated as a small product. It has a hypothesis, the telemetry it depends on, the YARA-L logic, the false positives I expect, the triage an analyst should follow, a tuning strategy, and a response action. If any one of those is missing, the detection is not done — no matter how clever the logic looks.

This is the workflow I run through, end to end:

1. Threat hypothesis
2. Required telemetry and UDM field validation
3. YARA-L detection logic
4. MITRE ATT&CK mapping
5. Expected false positives
6. Analyst triage steps
7. Response playbook
8. Tuning, suppression, and validation
9. Risk scoring and automation opportunities
10. Continuous improvement

If you only take one idea from this document, take this: **coverage is cheap, fidelity is expensive, and fidelity is what wins.**

---

## Who this is for

- Detection engineers writing and tuning rules in Google SecOps.
- SOC / MDR analysts who want to understand *why* a rule fired and what to do next.
- Security leads building a detection-as-code program with peer review and metrics.
- Hiring managers and interviewers evaluating how I think about detection engineering.

---

## Disclaimer

These detections are written as portfolio-grade YARA-L 2.0 examples. They must be validated inside a real Google Security Operations tenant before production use. UDM field availability depends on your log sources, parser quality, normalization, telemetry coverage, and environment.

Before enabling any rule, confirm:

- The required UDM fields are actually populated in your logs (use the UDM Lookup tool).
- Source logs are parsed correctly and consistently.
- The rule compiles in the SecOps Rules Editor.
- Alert volume is acceptable over a realistic historical window.
- Known-good administrative and automation activity is excluded.
- Severity, risk score, and response actions match your business risk.
- The detection output gives an analyst enough context to act.

Nothing here is offensive tooling. Every rule is defensive: it describes attacker *behavior* so a blue team can catch it.

---

# Part 1 — Detection Engineering Philosophy

## 1.1 Signals, detections, and alerts are not the same thing

People use these words interchangeably and it causes real damage.

- A **signal** is raw evidence: a process launched, a login happened, a connection was made.
- A **detection** is logic that turns one or more signals into a statement about *behavior*: "encoded PowerShell launched from a user-writable path with a network callback."
- An **alert** is a detection that we decided is worth a human's attention *right now*.

Not every detection should become an alert. Some detections are best left as risk contributors that only matter when stacked with others. Treating every detection as a page is how you burn out a SOC. Risk scoring (Part 4) is how we fix that.

## 1.2 The fidelity vs coverage trade-off

You can optimize a rule for **coverage** (catch every variation of a technique) or **fidelity** (fire only when it's almost certainly malicious). You usually can't max out both in one rule.

My rule of thumb:

- **High-fidelity, low-volume** detections become alerts on their own.
- **High-coverage, high-volume** detections become *risk contributors* — they raise an entity's risk score but only page when the score crosses a threshold or combines with something else.

Bad detection engineering tries to make a noisy coverage rule into a clean alerting rule by deleting everything that's annoying. Good detection engineering splits the difference deliberately and uses risk to manage volume.

## 1.3 The Pyramid of Pain still applies

When you decide *what* to detect, climb the pyramid. Hashes and IPs are trivial for an attacker to change. TTPs — behaviors — are expensive for them to change. So:

- Reference-list IOC matches (IPs, hashes, domains) are useful but brittle. Keep them, score them low-to-medium, and treat them as enrichment.
- Behavioral detections (encoded execution, suspicious parent/child chains, persistence patterns) are durable and deserve the engineering investment.

This is why most of the catalog below targets behavior, not indicators.

## 1.4 Every rule is a product with an owner

A rule with no owner is a rule that rots. Each detection should have:

- An owner who is accountable for its health.
- A review cadence.
- A documented expected response.
- Metrics: how often it fires, how often it's a true positive, how long triage takes.

If you can't answer "who owns this and is it still good?" the rule shouldn't be in production.

---

# Part 2 — Methodology

## 2.1 The detection hypothesis

Every rule starts with a hypothesis. The hypothesis is where 80% of the quality is decided.

**Weak:**

> Detect PowerShell.

**Strong:**

> Detect suspicious PowerShell execution where the command line shows encoded commands, hidden windows, execution-policy bypass, or download behavior — patterns associated with payload staging, defense evasion, and hands-on-keyboard intrusion — and raise risk on the executing host and user so it surfaces faster when combined with other signals.

A strong hypothesis answers five questions:

1. What specifically is suspicious?
2. Why does it matter to the business?
3. Which data source can *prove* it?
4. What false positives do I expect, and from where?
5. What should an analyst do when it fires?

If you can't answer all five, you're not ready to write YARA-L yet.

## 2.2 Telemetry requirements

Confirm the telemetry exists *before* writing logic. A perfect rule on a field your parser never populates is worth nothing.

| Detection area | Required telemetry |
| --- | --- |
| Identity compromise | IdP / SSO auth logs, IAM logs, MFA logs, conditional access logs |
| Endpoint execution | EDR process telemetry, Windows Security + Sysmon-equivalent logs |
| Lateral movement | Endpoint logs, auth logs, network/flow logs |
| Persistence | Process telemetry, registry events, scheduled task / service events |
| Privilege abuse | Directory audit logs, IAM change logs, group modification logs |
| Cloud abuse | Cloud audit logs (GCP/AWS/Azure), cloud IAM, storage access logs |
| Command and control | Network, firewall, proxy, DNS, EDR network telemetry |

For each rule, I write down the **minimum viable telemetry** — the fields the rule cannot work without — and the **enrichment telemetry** that makes triage faster but isn't strictly required.

## 2.3 The Alerting & Detection Strategy (ADS) skeleton

For anything beyond a trivial rule I document it against a lightweight ADS-style template. This is the structure I use for each detection in the catalog:

- **Goal** — the attacker behavior, in plain language.
- **Categorization** — MITRE tactic and technique.
- **Strategy abstract** — how the rule detects it, at a high level.
- **Technical context** — the UDM fields and log sources involved.
- **Blind spots** — what this rule will *not* catch (be honest).
- **False positives** — where benign activity looks the same.
- **Validation** — how to safely test it fires.
- **Priority / risk** — severity and risk score, and why.
- **Response** — what an analyst does.

The honest "blind spots" section is the part most engineers skip and the part that earns the most trust.

## 2.4 Rule quality standard

A production-quality detection includes, at minimum:

- Clear, namespaced rule name.
- Author and version.
- Description that states the behavior, not the keyword.
- Severity **and** a deliberate risk score.
- MITRE ATT&CK mapping.
- Required log source.
- Expected false positives.
- Actionable triage guidance.
- A suppression / exclusion strategy that uses reference lists, not hard-coded values.
- A test/validation plan.
- A defined response action.

---

# Part 3 — YARA-L 2.0, the way I actually use it

This section is the engineering core. If you understand these building blocks, the catalog reads easily.

## 3.1 Anatomy of a rule

```yaral
rule descriptive_namespaced_name {
  meta:
    // documentation: author, description, severity, MITRE, source, FP notes
  events:
    // the predicates that must be true; this is where filtering happens
  match:
    // OPTIONAL: the entity + time window to correlate events over
  outcome:
    // OPTIONAL: risk score and context variables computed per detection
  condition:
    // the trigger: which event variables must exist, plus thresholds
}
```

- **Single-event rules** evaluate one event at a time. `condition: $e` means "fire on any event that satisfies the events section." A single-event rule may set a constant `$risk_score` in `outcome`.
- **Multi-event rules** correlate events using a `match` section. The moment you correlate, any `outcome` variable must use an **aggregation function** — `count()`, `count_distinct()`, `sum()`, `max()`, `min()`, `avg()`, `stddev()`, `array_distinct()`. Even a constant risk score is written as `max(50)` in a multi-event rule.

## 3.2 The match section and correlation windows

`match` defines the grouping key and the sliding time window:

```yaral
match:
  $user over 5m         // group by user, 5-minute sliding window
```

```yaral
match:
  $user, $hostname over 10m   // group by the (user, host) pair
```

The variable you join on in `match` must be bound in the `events` section, and — critically for composite detections — must also be emitted in the `outcome` section of any upstream "producer" rule you want to chain.

You can also order events in time using `before` / `after` to express sequences (e.g., failures *before* a success).

## 3.3 Counting and thresholds in `condition`

- `#failed >= 5` counts the events bound to the `$failed` event variable.
- For distinct values of a *field*, don't try `#city` — compute `count_distinct()` in `outcome` and threshold the resulting variable in `condition`. This is the single most common beginner mistake, and the original version of this playbook had it. Fixed throughout below.

## 3.4 Reference lists — exclusions and IOC matching done right

Reference lists are how you keep tuning out of the rule body. Three flavors, three syntaxes:

```yaral
// STRING list — exact match
$e.principal.hostname in %approved_admin_hosts

// REGEX list — pattern match
$e.principal.process.command_line in regex %approved_automation_cmdlines

// CIDR list — IP-in-range match
$e.target.ip in cidr %threat_intel_ip_watchlist
```

For inline CIDR without a list, use the function:

```yaral
net.ip_in_range_cidr($e.principal.ip, "10.0.0.0/8")
```

**Why reference lists matter:** exclusions belong in data you can edit without touching the rule. Hard-coding `hostname != "JUMPBOX01"` into ten rules means ten edits and a peer review every time your jump-box estate changes. One reference list means one edit.

## 3.5 Outcome section and risk scoring

This is the modern heart of high-fidelity detection. The `outcome` section lets a rule compute a risk score and attach context.

```yaral
outcome:
  $risk_score = max(75)
  $risk_entity_to_score = $e.principal.hostname
  $command_lines = array_distinct($e.principal.process.command_line)
  $user = array_distinct($e.principal.user.userid)
```

Key facts to internalize:

- If you omit `$risk_score`, SecOps defaults it to **40** for alerting rules and **15** for non-alerting rules.
- `$risk_entity_to_score` tells the engine *which* entity to attribute the risk to (host, user, etc.). This is what makes entity-centric risk aggregation work.
- The stored value lands in `security_result.risk_score`, which downstream composite rules and dashboards can read.

## 3.6 Suppression windows

To stop a chatty rule from firing repeatedly on the same entity in a short span:

```yaral
outcome:
  $suppression_key = $hostname
options:
  suppression_window = 1h
```

This is far better than lowering severity to "hide" volume — a practice I treat as a tuning anti-pattern.

## 3.7 Composite (risk aggregation) detections

The payoff of risk scoring: build "producer" rules that emit risk on an entity, then a single "consumer" rule that fires only when an entity's *total* risk crosses a threshold. The consumer reads `RULE_DETECTION` events:

```yaral
rule host_risk_threshold_exceeded {
  meta:
    author = "Harshavardhan Malla"
    description = "Fires when a single host accumulates risk above threshold from multiple producer detections within 2h."
    severity = "Critical"
  events:
    $d.metadata.event_type = "RULE_DETECTION"
    $d.detection.detection.detection_depth = 0    // prevent feedback loops
    $d.detection.outcomes["risk_entity_to_score"] = $hostname
    $d.detection.risk_score = $risk
  match:
    $hostname over 2h
  outcome:
    $total_risk_score = sum($risk)
    $contributing_rules = array_distinct($d.detection.rule_name)
  condition:
    $d and $total_risk_score >= 90
}
```

This is how you let noisy-but-useful behavioral rules live at low risk individually, while still catching the host where five of them lit up in an hour.

## 3.8 Functions I reach for constantly

- `re.regex($field, \`(?i)pattern\`)` — case-insensitive pattern matching. The backticks avoid escaping hell.
- `net.ip_in_range_cidr($ip, "cidr")` — CIDR membership inline.
- `strings.to_lower()` / `strings.to_upper()` — normalize before comparing.
- `strings.concat()` / `strings.coalesce()` — build context strings, pick first non-empty field.
- `count()`, `count_distinct()`, `sum()`, `max()`, `min()`, `array_distinct()` — aggregation in `outcome`.

---

# Part 4 — The Detection Catalog

Each detection follows the same structure: **Hypothesis → Telemetry → Rule → MITRE → False positives → Triage → Tuning → Response.** I've grouped them by domain.

The reference lists used throughout (`%approved_admin_hosts`, `%approved_powershell_automation_accounts`, `%known_scanner_ips`, `%threat_intel_ip_watchlist`, etc.) live in `reference_lists/` and are referenced by name so tuning never touches rule logic.

See the individual rule files under `detections/` for the full YARA-L, and the per-domain notes below.

---

## ENDPOINT

### Detection E1 — Suspicious Encoded / Obfuscated PowerShell
**File:** `detections/endpoint/suspicious_encoded_powershell.yaral`

**Hypothesis.** An attacker uses encoded commands, hidden windows, profile bypass, or execution-policy bypass to run PowerShell that evades command-line inspection and analyst eyes. Legitimate admin tooling does some of this too — so this is a *risk contributor*, scored, not an auto-page on its own.

**Telemetry.** EDR / Sysmon process-launch events with `principal.process.command_line` populated. Minimum: command line, hostname, user. Enrichment: parent process, file hash.

**MITRE.** Execution / Defense Evasion — T1059.001, T1027.

**False positives.** SCCM, Intune Management Extension, Tanium, EDR live-response scripts, legitimate admin one-liners.

**Triage.**
1. Read the full command line. If encoded, decode the Base64 (it's UTF-16LE) and inspect.
2. Identify the parent and grandparent process. Office app or browser spawning PowerShell is far more suspicious than `cmd.exe` from an admin session.
3. Determine origin: interactive user, management tooling, or an unexpected process chain.
4. Pivot on host and user for surrounding process activity.
5. Look for network connections from the same process.
6. Check for file writes, persistence creation, and credential-access indicators.
7. If suspicious: isolate the endpoint and collect a forensic package.

**Tuning.** Add legitimate sources to `%approved_powershell_automation_accounts` and `%approved_admin_hosts` **only after** validating they are genuinely benign over a historical window. Never exclude all of PowerShell or all admins.

**Response.** Isolate host, kill process, revoke sessions if credential theft is suspected, block any extracted indicators, and consider a child detection for the specific TTP observed.

---

### Detection E2 — PowerShell Download Cradle
**File:** `detections/endpoint/powershell_download_cradle.yaral`

**Hypothesis.** Payload staging via PowerShell's web-download primitives. Combined with E1 on the same host, confidence rises sharply — which is exactly what risk aggregation is for.

**MITRE.** T1059.001, T1105.

**Triage.**
1. Extract URLs, domains, IPs, and file names from the command line.
2. Check domain age, reputation, hosting provider.
3. Pivot into proxy, DNS, firewall, and EDR network telemetry.
4. Determine whether the downloaded payload was then executed.
5. Check whether the same URL was reached by other hosts.
6. Block confirmed-malicious indicators.

**Response.** Same containment ladder as E1, plus enterprise-wide hunt for the URL/host and the downloaded file's hash.

---

### Detection E3 — LOLBin Proxy Execution (rundll32 / regsvr32 / mshta)
**File:** `detections/endpoint/lolbin_proxy_execution.yaral`

**Hypothesis.** Attackers use signed Windows binaries to proxy execution and bypass application control. The signal is a LOLBin invoking remote content or scriptlets.

**MITRE.** T1218 (.005 mshta, .010 regsvr32, .011 rundll32).

**Blind spot.** Won't catch LOLBins loading purely local malicious DLLs with no URL/scriptlet marker — pair with a parent/child anomaly rule.

**Triage.** Confirm the binary path, inspect the remote resource, check parent process (Office → LOLBin is a strong signal), and hunt the resource across the fleet.

---

### Detection E4 — Office Application Spawning a Command Interpreter
**File:** `detections/endpoint/office_spawns_shell.yaral`

**Hypothesis.** Macro/phishing execution: Word/Excel/Outlook spawning a shell or scripting host is rarely legitimate and is a classic initial-access tell.

**Telemetry note.** This rule lives or dies on parent-process normalization. Validate `principal.process.parent_process.file.full_path` is populated by your EDR parser before deploying.

**Triage.** Identify the originating document, pull it from the mail gateway, detonate in a sandbox, and check whether the spawned process pulled a second stage.

---

### Detection E5 — svchost Masquerading (wrong path)
**File:** `detections/endpoint/svchost_unusual_location.yaral`

**Hypothesis.** `svchost.exe` should only ever run from `System32` or `SysWOW64`. Anything else is masquerading. The original version matched on `command_line`; the correct, more reliable field is the resolved executable path.

**Triage.** Confirm the real path, pull the file hash and signature, review the parent (legit svchost is spawned by `services.exe`), inspect network connections, and hunt the hash fleet-wide. Quarantine or isolate if malicious.

---

### Detection E6 — Suspicious Scheduled Task Creation
**File:** `detections/endpoint/suspicious_scheduled_task_creation.yaral`

**Hypothesis.** `schtasks.exe` / `at.exe` creating tasks is a common persistence mechanism. Scored as medium because deployment tooling does this constantly — context is everything.

**Triage.** Review task name, schedule, and the `/tr` target. Tasks that launch binaries/scripts from user-writable directories (`AppData`, `Temp`, `ProgramData`) are high-suspicion. Hunt for identical task names across endpoints — attackers reuse them.

---

### Detection E7 — Suspicious Service Creation
**File:** `detections/endpoint/suspicious_service_creation.yaral`

**Hypothesis.** Services launched from temp/user paths, or created with `sc.exe`, are a durable persistence and lateral-movement primitive (think PsExec-style service installs).

**Triage.** Identify the service binary path, hash and signature it, check whether it was started, and hunt the binary across hosts.

---

## IDENTITY

### Detection I1 — Impossible Travel / Multi-City Login
**File:** `detections/identity/impossible_travel_multi_city_login.yaral`

**Hypothesis.** A single user authenticating successfully from multiple cities within a short window suggests credential or token compromise. The original used `#city > 1`, which doesn't count distinct field values correctly — fixed below with `count_distinct()`.

**Triage.** Review the source IPs and geolocations, MFA status and method, device trust and user agent. Compare against known VPN/proxy infra (`%approved_vpn_egress_ranges`). Look for risky sign-ins, mailbox rules, privilege changes, or data access. Revoke sessions and reset credentials if suspicious.

**Tuning.** Geo data is noisy. Keep this as a medium-risk contributor, not a standalone page, and lean on `%approved_vpn_egress_ranges`.

---

### Detection I2 — Brute Force Followed by Successful Login
**File:** `detections/identity/brute_force_followed_by_success.yaral`

**Hypothesis.** Multiple failures then a success for the same account, from the same source, within a window — credential guessing that worked.

**Telemetry note.** How a failed auth is represented varies by parser — some set `security_result.action = "BLOCK"`, some `"FAIL"`, some encode it only in `security_result.summary`. Confirm yours and adjust the predicate.

**Triage.** Confirm same-source for failures and success. Review device, IP, user agent, MFA result. Is the account privileged or a service account? Check for recent helpdesk/reset activity. Hunt post-login actions (mailbox, cloud console, VPN, privilege changes). Revoke, reset, disable if compromise is likely.

---

### Detection I3 — Password Spray (one source, many users)
**File:** `detections/identity/password_spray.yaral`

**Hypothesis.** Spraying flips brute force on its head: one source tries one or two passwords against many accounts to stay under per-account lockout thresholds. The tell is **distinct targeted users from a single source**.

**Triage.** Confirm the source is external/untrusted, count distinct users targeted, and — critically — check whether *any* of those users then logged in successfully from the same source. Block the source, force resets on any successful targets.

---

### Detection I4 — MFA Fatigue / Push Bombing
**File:** `detections/identity/mfa_fatigue_push_bombing.yaral`

**Hypothesis.** Attacker with valid creds spams MFA push prompts hoping the user approves one. The tell is many MFA challenges in a short window for one user, ending in an approval.

**Telemetry note.** MFA status field varies wildly by IdP (`security_result.detection_fields`, `security_result.summary`, custom labels). Map yours via the UDM Lookup tool. This rule is a *template* for the pattern, not a drop-in.

**Triage.** Confirm the prompt count, check whether a final approval succeeded, review the source IP/geography of the challenges, and contact the user out-of-band. Revoke sessions and re-register MFA if compromise is suspected.

---

### Detection I5 — Rapid User Creation and Deletion
**File:** `detections/identity/rapid_user_creation_deletion.yaral`

**Hypothesis.** An account created and deleted in a short span can indicate attacker cleanup, backdoor testing, or unauthorized lifecycle activity.

**Triage.** Identify who created and who deleted the account, what groups it held, whether it authenticated or touched sensitive systems before deletion, and whether a ticket/HR process backs it.

---

## PRIVILEGE & CLOUD

### Detection P1 — Privileged Group Modification
**File:** `detections/privilege/privileged_group_modification.yaral`

**Hypothesis.** Additions to high-privilege groups (Domain/Enterprise Admins, Global Administrator, etc.) are among the highest-value events in any environment.

**Triage.** Identify actor and target, confirm a change ticket/approval, review the actor's recent auth history, watch the target account's post-change activity, and check whether privilege was removed shortly after use (a hallmark of abuse). Remove membership, revoke sessions, and investigate the actor if unauthorized.

---

### Detection P2 — Outbound Connection to Threat-Intel IP Watchlist
**File:** `detections/network/outbound_connection_to_watchlist_ip.yaral`

**Hypothesis.** A host connecting to a known-bad IP. Useful but brittle (Pyramid of Pain) — so it's enrichment-grade risk, validated against shared-hosting/sinkhole noise.

**Triage.** Identify source host/user, the destination's reputation and associated malware families, whether the connection was allowed or blocked, and which other hosts touched the same IP. Confirm it isn't shared hosting/CDN/sinkhole before escalating. Block if confirmed; isolate the host if it looks like live C2.

---

### Detection P3 — Cloud IAM Privileged Role Grant (GCP)
**File:** `detections/cloud/gcp_privileged_iam_role_grant.yaral`

**Hypothesis.** In cloud, the equivalent of "add to Domain Admins" is binding a principal to `owner`, `editor`, or `*Admin` roles. These grants are prime persistence and escalation moves.

**Telemetry note.** UDM field paths for cloud IAM vary by source/parser version; confirm `target.resource.attribute.roles.name` and the product event type against your tenant's normalized GCP audit logs.

**Triage.** Identify actor and grantee, confirm an IaC/change ticket, check whether the grant was via an interactive user or a compromised service account, and review what the grantee did after the grant.

---

# Part 5 — Triage Playbooks

See `playbooks/` for full runbooks. Summaries below.

## 5.1 Suspicious PowerShell Triage

**Escalate to High when combined with:** encoded command, download cradle, hidden execution, bypass flags, suspicious parent (Office/browser), network callback, or execution from a user-writable path.

**Response.** Isolate endpoint · kill process · quarantine payload · revoke sessions · reset creds if theft suspected · block indicators · add a targeted child detection.

## 5.2 Identity Compromise Triage

**Escalate to High when the alert includes:** failures-then-success, impossible travel, MFA fatigue, new-device sign-in, risky IP, privileged account, unusual user agent, or post-login privilege changes.

**Response.** Revoke sessions · reset password · re-register MFA · temporarily disable account · block source · audit for persistence · notify user and management out-of-band.

## 5.3 Endpoint Persistence Triage

**Common persistence sources:** scheduled tasks, services, Run keys, startup folder, WMI subscriptions, new local admins, DLL search-order hijacking, browser extensions.

**Response.** Disable the mechanism · remove files · isolate endpoint · collect forensics · hunt the pattern fleet-wide · add detection logic for the specific variant.

## 5.4 Threat-Intel Match Triage

**Response.** Block indicator · isolate endpoint · enterprise-wide exposure search · push indicator to watchlists · strengthen the rule's context · document the outcome.

## 5.5 Severity & response matrix

| Severity | Risk score band | SLA to first action | Default response |
| --- | --- | --- | --- |
| Critical | 90+ (often composite) | Immediate | Isolate + invoke IR |
| High | 70–89 | < 30 min | Investigate, contain if confirmed |
| Medium | 40–69 | < 4 hours | Triage, enrich, watch |
| Low / contributor | < 40 | Batched review | Feeds risk aggregation only |

---

# Part 6 — Tuning, False Positives, and Suppression

## 6.1 Tune on evidence, not annoyance

The cardinal sin is deleting logic because it's noisy without understanding *why*. Run the rule over 7, 14, and 30 days of history. Bucket the matches. Identify the top false-positive sources by host, user, and command line. Then make a deliberate decision.

**Good exclusions:**

- Approved automation accounts (in a reference list).
- Known admin/jump hosts (in a reference list).
- Approved software-deployment paths.
- Internal vulnerability-scanner IPs.

**Anti-patterns I refuse to ship:**

- Excluding *all* admin activity.
- Excluding entire subnets without per-host review.
- Permanently excluding a noisy user instead of fixing the logic.
- Lowering severity to *hide* volume rather than reduce it.

## 6.2 Exclusions live in reference lists, not rule bodies

Every exclusion in the catalog above is a reference list (`%approved_admin_hosts`, `%approved_powershell_automation_accounts`, `%known_scanner_ips`, `%approved_vpn_egress_ranges`, `%approved_iac_service_accounts`, `%threat_intel_ip_watchlist`). Editing a list is a data change with an owner and a reason — not a rule edit that needs a fresh peer review every time.

## 6.3 Suppression vs reduction

When a rule is legitimately repetitive on the same entity, use a `suppression_window` keyed on the entity rather than weakening the detection:

```yaral
outcome:
  $suppression_key = $hostname
options:
  suppression_window = 1h
```

## 6.4 Rule tuning checklist

- [ ] Rule compiles in the Rules Editor.
- [ ] All referenced UDM fields are populated in your logs.
- [ ] Historical test run over 7, 14, 30 days.
- [ ] Alert volume reviewed and acceptable.
- [ ] Top false-positive sources identified.
- [ ] Admin / automation / scanner exclusions added via reference lists.
- [ ] Service-account exclusions added only when justified.
- [ ] Severity and risk score match business risk.
- [ ] Triage steps are concrete and actionable.
- [ ] Detection output carries useful context (`outcome` variables).
- [ ] Mapped to MITRE ATT&CK.
- [ ] Owner assigned and review cadence set.
- [ ] Expected response action documented.

---

# Part 7 — Detection-as-Code

Detection logic is software. Treat it that way.

## 7.1 Repository structure

```text
google-secops-yaral-detection-playbook/
│
├── README.md
├── detections/
│   ├── identity/
│   ├── endpoint/
│   ├── network/
│   ├── privilege/
│   ├── cloud/
│   └── composite/
├── playbooks/
├── reference_lists/
├── tests/
│   └── unit_events/
└── docs/
```

## 7.2 Workflow

1. **Branch** per detection or change.
2. **Peer review** every rule. A second engineer checks the hypothesis, the blind spots, and the FP analysis — not just the syntax.
3. **CI validation:** lint YARA-L, confirm it compiles, and run each rule against the `tests/unit_events/` fixtures (a known true-positive event that must match, a known false-positive event that must not).
4. **Version** every rule (`rule_version` in `meta`) and record changes in commit messages.
5. **Promote** to production only after the tuning checklist passes.

## 7.3 Commit standards

```text
feat(identity): add password spray detection (T1110.003)
feat(endpoint): add Office-spawns-interpreter detection
fix(identity): correct impossible-travel distinct-city counting
tune(endpoint): move PowerShell exclusions to reference list
docs(mitre): refresh ATT&CK coverage map
```

---

# Part 8 — Metrics and Detection Health

You can't manage what you don't measure. The detections I trust are the ones with numbers behind them.

**Per-rule metrics.**

- **Volume** — detections/day. Spikes mean a parser, source, or environment change to investigate.
- **Precision (TP rate)** — true positives ÷ total. Below a threshold, the rule goes back to tuning.
- **Time-to-triage** — how long an analyst spends. High time means the `outcome` context is weak.
- **Last fired / last reviewed** — staleness indicators.

**Program-level metrics.**

- **MITRE coverage** — techniques covered vs the ATT&CK matrix, weighted by relevance to your threat model. Coverage breadth is not the goal; *meaningful* coverage is.
- **Detection health** — share of rules with an owner, a playbook, a test fixture, and a recent review.
- **Mean time to detect (MTTD)** for validated incidents.

A detection-health dashboard that surfaces "rules with no owner," "rules that haven't fired in 90 days," and "rules below precision target" is worth more than another fifty raw detections.

---

# Part 9 — MITRE ATT&CK Mapping

| Detection | Tactic | Technique |
| --- | --- | --- |
| Suspicious Encoded PowerShell | Execution, Defense Evasion | T1059.001, T1027 |
| PowerShell Download Cradle | Execution, Command and Control | T1059.001, T1105 |
| LOLBin Proxy Execution | Defense Evasion | T1218.005/.010/.011 |
| Office Spawns Interpreter | Execution, Initial Access | T1059, T1566.001, T1204.002 |
| svchost Masquerading | Defense Evasion | T1036.005 |
| Suspicious Scheduled Task | Persistence, Priv. Esc. | T1053.005 |
| Suspicious Service Creation | Persistence, Lateral Movement | T1543.003, T1569.002 |
| Impossible Travel | Initial Access, Credential Access | T1078 |
| Brute Force → Success | Credential Access, Initial Access | T1110, T1078 |
| Password Spray | Credential Access | T1110.003 |
| MFA Push Bombing | Credential Access | T1621 |
| Rapid User Create/Delete | Persistence, Defense Evasion | T1136, T1070 |
| Privileged Group Modification | Priv. Esc., Persistence | T1098, T1078.003 |
| Threat-Intel IP Match | Command and Control | T1071 |
| GCP Privileged Role Grant | Priv. Esc., Persistence | T1098, T1078.004 |
| Host Risk Threshold (composite) | — (meta-detection) | aggregates the above |

---

# Part 10 — Detection Lifecycle

**Stage 1 — Hypothesis.** Define the attacker behavior in one honest sentence.
**Stage 2 — Telemetry validation.** Confirm the logs contain process name, command line, hostname, user, parent process, timestamp, and (ideally) file hash. Use the UDM Lookup tool.
**Stage 3 — Draft.** Write the initial rule. Pick single-event vs multi-event deliberately.
**Stage 4 — Historical testing.** Run over history. Measure count, unique hosts, unique users, top command lines, known-good automation, and the suspicious outliers.
**Stage 5 — Tuning.** Tune on evidence. Add reference-list exclusions. Set risk score and severity.
**Stage 6 — Production.** Deploy only when it compiles, volume is manageable, triage is clear, response is defined, and the business owner accepts the residual risk.
**Stage 7 — Continuous improvement.** Re-review after FP spikes, incident lessons, new intel, parser changes, log-source changes, business-process changes, and new attacker techniques.

---

# Part 11 — Production Hardening Roadmap

1. Convert high-volume behavioral rules into **risk contributors** feeding composite detections.
2. Maintain reference lists for approved admin, automation, scanner, and VPN activity.
3. Add **entity context** for crown-jewel users and servers so risk scoring weights them higher.
4. Add suppression windows for known repetitive-but-benign sources.
5. Stand up a **detection-health dashboard** (ownership, staleness, precision, volume).
6. Automate IP/domain/hash reputation enrichment at alert time.
7. Integrate **SOAR** for containment and session revocation on Critical/composite alerts.
8. Run the full thing as **detection-as-code**: branches, peer review, CI compile + unit-event tests, versioning.

---

# Interview Talking Points

This playbook demonstrates that I can:

- Translate attacker behavior into durable, behavior-first detection logic.
- Write modern YARA-L 2.0 for Google SecOps — multi-event correlation, `outcome` risk scoring, reference lists, suppression windows, and composite/risk-aggregation detections.
- Work fluently with UDM-normalized telemetry across identity, endpoint, network, and cloud.
- Map detections to MITRE ATT&CK and reason about coverage vs fidelity instead of chasing raw rule counts.
- Think past alert creation into triage, response, and measurable detection health.
- Reduce false positives with reference lists, evidence-based tuning, and suppression — never by hiding volume.
- Run detection engineering as code, with peer review, CI validation against unit events, and versioning.

---

# Summary

Detection engineering is not writing rules. It is building small, accountable products that turn telemetry into decisions.

A good detection is:

- **Technically valid** — it compiles and uses fields that actually exist.
- **Behavior-first** — it targets TTPs, not throwaway indicators.
- **Telemetry-aware** — it depends only on data you reliably have.
- **Tuned for reality** — exclusions live in reference lists, volume is managed with risk and suppression, never by hiding it.
- **Analyst-usable** — it carries the context needed to triage and a playbook for what to do.
- **Risk-scored** — it contributes to an entity's risk so noisy-but-useful signals surface when they stack.
- **Measured and owned** — someone is accountable, and the numbers say whether it's still good.
- **Continuously improved** — it changes as attackers, parsers, and the business change.

Build detections like products, score them like a risk model, tune them like an engineer, and hand them to analysts like a teammate who already did the hard thinking. That's the difference between a pile of alerts and a detection program.

— *Harshavardhan Malla*
