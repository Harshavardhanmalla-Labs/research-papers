# Suspicious PowerShell Triage Playbook

**Owner:** Harshavardhan Malla
**Related detections:** E1 (encoded PowerShell), E2 (download cradle), E3 (LOLBin proxy execution)

## Escalation criteria
Escalate to High when the alert includes any of:
- encoded command (`-enc` / Base64 blob)
- download cradle (`Invoke-WebRequest`, `DownloadString`, `BITSTransfer`, etc.)
- hidden window or profile/policy bypass
- suspicious parent (Office, browser, mail client, scripting host)
- network callback during the process lifetime
- execution from a user-writable path (`AppData`, `Temp`, `ProgramData`, `Users\Public`)

## Investigation steps
1. Pull the full process tree (parent, grandparent, children).
2. Read and decode the command line. PowerShell Base64 is UTF-16LE.
3. Extract URLs, IPs, domains, file paths, hashes.
4. Determine whether a payload was downloaded and whether it was then executed.
5. Search the same command line and hash across the environment.
6. Review network activity from the process — DNS, proxy, firewall, EDR.
7. Check for persistence created in the same session (scheduled tasks, services, Run keys).
8. Contain if malicious.

## Response actions
- Isolate the endpoint via EDR.
- Kill the process and any child processes.
- Quarantine any dropped payload.
- Revoke active sessions for the executing user.
- Reset credentials if credential theft is suspected.
- Block extracted indicators (URL, domain, IP, hash) at gateway / EDR / DNS.
- Open a child detection for the specific TTP if it's new.
