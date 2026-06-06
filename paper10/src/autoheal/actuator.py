"""Stage 5: Actuator — simulate patch application with realistic failure modes.

The failure-mode distribution is pre-registered (PAPER10_PROTOCOL.md §3 Stage 5):
  success: 92%
  rollback: 5% (post-patch health-check fails)
  defer:    3% (patch blocked at install time)

These rates are drawn from public sysadmin literature on patch-success
rates in production environments; specific numbers are pre-registered
constants for the simulation.
"""
from __future__ import annotations
from enum import Enum
import numpy as np


class ActionOutcome(str, Enum):
    SUCCESS  = "SUCCESS"
    ROLLBACK = "ROLLBACK"
    DEFERRED = "DEFERRED"


# Pre-registered failure-mode distribution (locked).
P_SUCCESS  = 0.92
P_ROLLBACK = 0.05
P_DEFERRED = 0.03
assert abs(P_SUCCESS + P_ROLLBACK + P_DEFERRED - 1.0) < 1e-6


def simulate_action(
    rng: np.random.Generator,
    in_kev: bool = False,
) -> ActionOutcome:
    """Simulate one patch action.

    The distribution is pre-registered; in_kev is logged for verification
    purposes but does not change the action-success rate. Realistic real-
    world data would condition on package, OS, and patch type; AutoHeal's
    simulation assumes the pre-registered distribution to keep the threat
    model identifiable.
    """
    r = rng.random()
    if r < P_SUCCESS:
        return ActionOutcome.SUCCESS
    if r < P_SUCCESS + P_ROLLBACK:
        return ActionOutcome.ROLLBACK
    return ActionOutcome.DEFERRED
