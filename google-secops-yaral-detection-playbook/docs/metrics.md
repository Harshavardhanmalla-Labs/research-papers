# Detection Health Metrics

## Per-rule metrics
- **Volume** — detections/day. Spikes warrant a parser / source / environment review.
- **Precision (TP rate)** — true positives ÷ total. Below threshold, rule returns to tuning.
- **Time-to-triage** — analyst minutes per alert. High time → weak `outcome` context.
- **Last fired / last reviewed** — staleness indicators.

## Program-level metrics
- **MITRE coverage** — techniques covered vs the ATT&CK matrix, weighted by relevance to the threat model.
- **Detection health** — share of rules with an owner, a playbook, a test fixture, and a recent review.
- **Mean time to detect (MTTD)** for validated incidents.

A detection-health dashboard surfacing "rules with no owner," "rules that haven't fired in 90 days," and "rules below precision target" is worth more than another fifty raw detections.
