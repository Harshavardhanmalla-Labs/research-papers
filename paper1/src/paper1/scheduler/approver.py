"""Human-approval policies A and B.

Each policy derives a per-pair deterministic RNG from (seed, pair_id), so
approval decisions are reproducible and independent of call order. The
KEV-deadline override is checked first under both policies. The risk
acceptance pathway records a POA&M-style decision; it does not assert
compliance.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from paper1.utils.seeds import derive_subseed, make_rng

__all__ = [
    "ApprovalDecision",
    "ApproverPolicyA",
    "ApproverPolicyB",
    "BaseApproverPolicy",
    "load_approver_policy",
    "make_approver",
]

RISK_EXPIRATION_DAYS = 90
RISK_REVIEW_TRIGGER = "KEV_ADDED"
RISK_COMPENSATING_CONTROLS = ["network_isolation"]


@dataclass(frozen=True)
class ApprovalDecision:
    decision: Literal["approved", "deferred", "accepted_risk"]
    approver_id: str
    delay_days: int
    reason: str
    risk_acceptance: dict[str, Any] | None = field(default=None)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _parse_due(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _kev_override(pair_row: Mapping[str, Any], now: datetime, hours: int = 48) -> bool:
    due = _parse_due(pair_row.get("kev_due_date"))
    if due is None:
        return False
    deadline = datetime.combine(due, datetime.max.time(), tzinfo=now.tzinfo)
    return deadline <= now + timedelta(hours=hours)


def _complexity(pair_row: Mapping[str, Any]) -> float:
    v = pair_row.get("complexity_score")
    if v is None:
        return 0.0
    return float(v)


def _risk_payload(pair_row: Mapping[str, Any], now: datetime, approver_id: str) -> dict[str, Any]:
    return {
        "risk_acceptance_reason": "Remediation deferred under policy; residual risk accepted.",
        "risk_acceptance_compensating_controls": list(RISK_COMPENSATING_CONTROLS),
        "risk_acceptance_expiration_date": (now.date() + timedelta(days=RISK_EXPIRATION_DAYS)),
        "risk_acceptance_review_trigger": RISK_REVIEW_TRIGGER,
        "risk_acceptance_approver_id": approver_id,
    }


class BaseApproverPolicy:
    policy_name = "base"
    rho_senior = 0.7

    def __init__(self, seed: int = 0, config: Mapping[str, Any] | None = None):
        self.seed = int(seed)
        self.config = dict(config or {})
        self.rho_senior = float(self.config.get("rho_senior", self.rho_senior))

    @property
    def approver_id(self) -> str:
        return f"approver:{self.policy_name}"

    def _rng(self, pair_id: str):
        return make_rng(derive_subseed(self.seed, f"approver|{self.policy_name}|{pair_id}"))

    def approve(self, pair_row: Mapping[str, Any], now: datetime) -> ApprovalDecision:  # pragma: no cover
        raise NotImplementedError


class ApproverPolicyA(BaseApproverPolicy):
    policy_name = "A"

    def approve(self, pair_row: Mapping[str, Any], now: datetime) -> ApprovalDecision:
        pid = str(pair_row["pair_id"])
        if _kev_override(pair_row, now, int(self.config.get("kev_breach_override_hours", 48))):
            return ApprovalDecision("approved", self.approver_id, 0, "KEV_OVERRIDE_APPROVED")
        if _complexity(pair_row) <= self.rho_senior:
            return ApprovalDecision("approved", self.approver_id, 0, "LOW_COMPLEXITY_APPROVED")
        # High complexity: probabilistic senior review.
        r = float(self._rng(pid).random())
        approve_p = float(self.config.get("elevated_approval_probability", 0.85))
        if r < approve_p:
            return ApprovalDecision("approved", self.approver_id, 0, "HIGH_COMPLEXITY_APPROVED")
        if r < approve_p + 0.10:
            return ApprovalDecision("deferred", self.approver_id, 14, "HIGH_COMPLEXITY_DEFERRED")
        return ApprovalDecision(
            "accepted_risk",
            self.approver_id,
            0,
            "HIGH_COMPLEXITY_RISK_ACCEPTED",
            risk_acceptance=_risk_payload(pair_row, now, self.approver_id),
        )


class ApproverPolicyB(BaseApproverPolicy):
    policy_name = "B"

    def approve(self, pair_row: Mapping[str, Any], now: datetime) -> ApprovalDecision:
        pid = str(pair_row["pair_id"])
        if _kev_override(pair_row, now, int(self.config.get("kev_breach_override_hours", 48))):
            return ApprovalDecision("approved", self.approver_id, 0, "KEV_OVERRIDE_APPROVED")
        low_delay = int(self.config.get("low_complexity_delay_business_days", 1))
        if _complexity(pair_row) <= self.rho_senior:
            return ApprovalDecision("approved", self.approver_id, low_delay, "LOW_COMPLEXITY_CAB_APPROVED")
        cab_delay = int(self.config.get("high_complexity_cab_cadence_business_days", 5))
        extra = int(self.config.get("restricted_zone_additional_delay_business_days", 5))
        if pair_row.get("host_role") == "restricted_zone_system":
            p_accept = float(self.config.get("risk_acceptance_probability_high_complexity_restricted", 0.15))
            if float(self._rng(pid).random()) < p_accept:
                return ApprovalDecision(
                    "accepted_risk",
                    self.approver_id,
                    0,
                    "RESTRICTED_HIGH_COMPLEXITY_RISK_ACCEPTED",
                    risk_acceptance=_risk_payload(pair_row, now, self.approver_id),
                )
            return ApprovalDecision(
                "approved", self.approver_id, cab_delay + extra, "RESTRICTED_HIGH_COMPLEXITY_CAB_APPROVED"
            )
        return ApprovalDecision("approved", self.approver_id, cab_delay, "HIGH_COMPLEXITY_CAB_APPROVED")


def load_approver_policy(path_or_name: str | Path) -> dict[str, Any]:
    """Load an approver policy config by path or short name ('a'/'b')."""
    import yaml

    p = Path(path_or_name)
    if not p.exists():
        name = str(path_or_name).lower()
        p = _repo_root() / "configs" / f"approver_policy_{name}.yaml"
    if not p.exists():
        raise FileNotFoundError(f"approver policy config not found: {path_or_name}")
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def make_approver(policy_name_or_config: str | Mapping[str, Any], seed: int = 0) -> BaseApproverPolicy:
    """Construct an approver policy from a name ('A'/'B') or a config dict."""
    if isinstance(policy_name_or_config, Mapping):
        config = dict(policy_name_or_config)
        name = str(config.get("policy_name", "A")).upper()
    else:
        name = str(policy_name_or_config).upper()
        config = {}
        # Best-effort: load the matching config file if present.
        try:
            config = load_approver_policy(name.lower())
        except FileNotFoundError:
            config = {}
    if name == "A":
        return ApproverPolicyA(seed=seed, config=config)
    if name == "B":
        return ApproverPolicyB(seed=seed, config=config)
    raise ValueError(f"unknown approver policy {name!r}")
