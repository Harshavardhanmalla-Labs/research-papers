"""AutoHeal — A Self-Healing Framework for Autonomous Vulnerability Remediation.

Synthesizes Papers 3-9: uses EEHDA generator (Paper 3), HygienePrio scorer
(Paper 4), Paper 5 multi-window simulator, Paper 7 lag-1 calibration,
Paper 9 self-trajectory convention, and real_data/ CVE corpus.

Pre-registered protocol: paper10/design/PAPER10_PROTOCOL.md
"""
from .framework import AutoHeal, AutoHealConfig, run_window
from .triage import classify, TriageClass
from .actuator import simulate_action, ActionOutcome
from .verifier import health_check
