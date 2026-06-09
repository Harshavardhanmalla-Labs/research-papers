# MITRE ATT&CK Coverage Map

| Detection | Tactic | Technique |
| --- | --- | --- |
| Suspicious Encoded PowerShell | Execution, Defense Evasion | T1059.001, T1027 |
| PowerShell Download Cradle | Execution, Command and Control | T1059.001, T1105 |
| LOLBin Proxy Execution | Defense Evasion | T1218.005 / .010 / .011 |
| Office Spawns Interpreter | Execution, Initial Access | T1059, T1566.001, T1204.002 |
| svchost Masquerading | Defense Evasion | T1036.005 |
| Suspicious Scheduled Task | Persistence, Privilege Escalation | T1053.005 |
| Suspicious Service Creation | Persistence, Lateral Movement | T1543.003, T1569.002 |
| Impossible Travel | Initial Access, Credential Access | T1078 |
| Brute Force → Success | Credential Access, Initial Access | T1110, T1078 |
| Password Spray | Credential Access | T1110.003 |
| MFA Push Bombing | Credential Access | T1621 |
| Rapid User Create/Delete | Persistence, Defense Evasion | T1136, T1070 |
| Privileged Group Modification | Privilege Escalation, Persistence | T1098, T1078.003 |
| Threat-Intel IP Match | Command and Control | T1071 |
| GCP Privileged Role Grant | Privilege Escalation, Persistence | T1098, T1078.004 |
| Host Risk Threshold (composite) | Meta-detection | aggregates the above |
