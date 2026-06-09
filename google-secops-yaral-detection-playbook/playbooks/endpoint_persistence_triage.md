# Endpoint Persistence Triage Playbook

**Owner:** Harshavardhan Malla
**Related detections:** E6 (scheduled tasks), E7 (service creation), and any future Run-key / WMI / startup-folder rules.

## Common persistence sources
- Scheduled tasks (`schtasks.exe`, `at.exe`, Task Scheduler XML)
- Services (`sc.exe`, service installs, ServiceDLL changes)
- Registry Run / RunOnce keys
- Startup folder shortcuts
- WMI event subscriptions
- New local administrators
- DLL search-order hijacking
- Browser extensions and Office add-ins

## Investigation steps
1. Identify the persistence mechanism, creation time, and modifying user.
2. Identify the creating process tree.
3. Validate the executable path, hash, and digital signature.
4. Search the same pattern (task name, service name, registry value, file path) fleet-wide.
5. Check network activity and whether the persistence has actually executed.
6. Correlate with prior alerts on the same host or user.

## Response actions
- Disable the persistence mechanism.
- Remove dropped files.
- Isolate the endpoint.
- Collect forensic artifacts (memory, registry hives, event logs).
- Hunt the pattern across the fleet.
- Add a targeted detection for the specific variant if it's novel.
