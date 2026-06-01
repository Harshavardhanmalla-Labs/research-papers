"""Capacity-constrained scheduler (Phase 8).

Consumes a ranked queue (Phase 5/7), applies blackout windows,
operational constraints (group caps, dependency staging, domain-controller
staged rollout), and a human-approval policy, then records every decision
as a hash-chained AuditDecisionRecord. No remediation is performed; the
scheduler only schedules and records decisions.
"""

from paper1.scheduler.approver import (
    ApprovalDecision,
    ApproverPolicyA,
    ApproverPolicyB,
    BaseApproverPolicy,
    load_approver_policy,
    make_approver,
)
from paper1.scheduler.blackout import (
    BlackoutDecision,
    blackout_active,
    is_business_hours,
    is_cab_blackout,
    is_in_maintenance_window,
    load_blackout_config,
)
from paper1.scheduler.constraints import (
    ConstraintResult,
    all_constraints_satisfied,
    check_dependency,
    check_domain_controller_staging,
    check_group_cap,
    dc_first_succeeded,
    dependency_satisfied,
    group_cap_violated,
)
from paper1.scheduler.risk_acceptance import (
    accept_risk,
    reawaken_expired_acceptances,
    review_trigger_fired,
    validate_risk_acceptance_payload,
)
from paper1.scheduler.scheduler import (
    DeferredPair,
    ScheduledPair,
    ScheduleResult,
    add_business_days,
    schedule_window,
)

__all__ = [
    "ApprovalDecision",
    "ApproverPolicyA",
    "ApproverPolicyB",
    "BaseApproverPolicy",
    "BlackoutDecision",
    "ConstraintResult",
    "DeferredPair",
    "ScheduleResult",
    "ScheduledPair",
    "accept_risk",
    "add_business_days",
    "all_constraints_satisfied",
    "blackout_active",
    "check_dependency",
    "check_domain_controller_staging",
    "check_group_cap",
    "dc_first_succeeded",
    "dependency_satisfied",
    "group_cap_violated",
    "is_business_hours",
    "is_cab_blackout",
    "is_in_maintenance_window",
    "load_approver_policy",
    "load_blackout_config",
    "make_approver",
    "reawaken_expired_acceptances",
    "review_trigger_fired",
    "schedule_window",
    "validate_risk_acceptance_payload",
]
