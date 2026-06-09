# Unit Event Fixtures

For each rule under `detections/`, this folder should hold:

- `<rule_name>.tp.json` — a UDM event that the rule **must** match.
- `<rule_name>.fp.json` — a UDM event that the rule **must not** match.

These are wired into CI so a rule edit that silently breaks the true positive — or starts matching the known false positive — fails the build. Fixtures are intentionally minimal: only the fields the rule reads, plus enough metadata to look like a real event.
