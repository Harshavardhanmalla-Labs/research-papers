"""Stage 6: Verifier — post-action health checks + cascading-failure detection.

The health check is deterministic from the seed; the cascading-failure
detector triggers when more than 5 rollbacks share a common patch
ancestor (here approximated by a common CVE-id prefix indicating a
shared upstream package).
"""
from __future__ import annotations
from collections import Counter
from typing import List


# Pre-registered cascading-failure threshold (PAPER10_PROTOCOL.md §3).
CASCADE_THRESHOLD = 5


def health_check(was_success: bool) -> bool:
    """Return True if the post-action state is healthy.

    With pre-registered failure-mode distribution, this is identity with
    the action outcome: a SUCCESS action passes health check, anything
    else does not. Real deployments would run sophisticated post-action
    probes here (process health, configuration drift checks, performance
    regression tests).
    """
    return was_success


def detect_cascade(rollback_cve_ids: List[str]) -> bool:
    """Heuristic cascading-failure detector.

    Returns True if more than CASCADE_THRESHOLD rollbacks share a common
    CVE-id prefix (interpreted as a shared upstream patch source). In
    AutoHeal, this triggers a hard-stop and human escalation.
    """
    if len(rollback_cve_ids) <= CASCADE_THRESHOLD:
        return False
    # Use first 5 characters of the CVE prefix as the "ancestor" signal;
    # in practice this corresponds to the publication year of the
    # disclosed parent CVE.
    prefixes = [cve_id[:9] for cve_id in rollback_cve_ids if isinstance(cve_id, str)]
    counts = Counter(prefixes)
    return any(c > CASCADE_THRESHOLD for c in counts.values())
