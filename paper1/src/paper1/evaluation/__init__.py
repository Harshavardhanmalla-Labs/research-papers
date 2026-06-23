"""Evaluation metrics + statistical analysis layer (Phases 9-10).

Ranking-quality metrics, simulated expected exploited-host-days (EEHDA),
compliance / operational-efficacy metrics, audit-trail metrics, and
scheduler-derived metrics (Phase 9), plus paired statistical-comparison
helpers -- bootstrap CIs, the Wilcoxon signed-rank test, Holm-Bonferroni
correction, paired effect sizes, and minimum-detectable-effect (Phase 10).
Experiment runners and aggregation arrive in later phases.
"""

from paper1.evaluation.audit_metrics import (
    audit_explanation_completeness,
    audit_record_count_by_type,
    hash_chain_validity,
    imputation_rate_per_feature,
)
from paper1.evaluation.compliance_metrics import (
    capacity_efficiency,
    kev_deadline_breach_rate,
    kev_remediation_latency,
)
from paper1.evaluation.eehda import (
    compute_ehd,
    compute_pair_ehd,
    eehda_absolute,
    eehda_relative,
    eehda_report,
    fraction_of_oracle,
)
from paper1.evaluation.metrics import (
    aggregate_metrics,
    validate_metric_frame,
)
from paper1.evaluation.ranking_metrics import (
    ndcg_at_k,
    precision_at_k,
    rank_churn,
    ranking_curve_at_ks,
    recall_at_k,
)
from paper1.evaluation.scheduler_metrics import (
    deferred_count,
    escalation_count,
    poam_review_trigger_compliance,
    risk_acceptance_rate,
    scheduled_count,
    scheduler_feasibility_rate,
)
from paper1.evaluation.statistical_tests import (
    StatTestResult,
    bootstrap_ci,
    bootstrap_ci_bca,
    clean_numeric_array,
    compare_many_to_baseline,
    compare_to_baseline,
    holm_bonferroni,
    minimum_detectable_effect,
    paired_arrays,
    paired_bootstrap_ci,
    paired_cohens_d,
    paired_mean_difference,
    relative_difference,
    validate_per_seed_metric_frame,
    wilcoxon_signed_rank,
)

__all__ = [
    "StatTestResult",
    "aggregate_metrics",
    "audit_explanation_completeness",
    "audit_record_count_by_type",
    "bootstrap_ci",
    "bootstrap_ci_bca",
    "capacity_efficiency",
    "clean_numeric_array",
    "compare_many_to_baseline",
    "compare_to_baseline",
    "compute_ehd",
    "compute_pair_ehd",
    "deferred_count",
    "eehda_absolute",
    "eehda_relative",
    "eehda_report",
    "escalation_count",
    "fraction_of_oracle",
    "hash_chain_validity",
    "holm_bonferroni",
    "imputation_rate_per_feature",
    "kev_deadline_breach_rate",
    "kev_remediation_latency",
    "minimum_detectable_effect",
    "ndcg_at_k",
    "paired_arrays",
    "paired_bootstrap_ci",
    "paired_cohens_d",
    "paired_mean_difference",
    "poam_review_trigger_compliance",
    "precision_at_k",
    "rank_churn",
    "ranking_curve_at_ks",
    "recall_at_k",
    "relative_difference",
    "risk_acceptance_rate",
    "scheduled_count",
    "scheduler_feasibility_rate",
    "validate_metric_frame",
    "validate_per_seed_metric_frame",
    "wilcoxon_signed_rank",
]
