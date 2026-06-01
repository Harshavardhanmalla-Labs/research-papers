"""
HygienePrio: Cyber-Hygiene Signal Augmentation for EPSS-Weighted
Vulnerability Prioritization.

Paper 4 of the VulnPrio / HygieneBench research sequence.
All results are bounded to the synthetic EEHDA fleet evaluation context.
"""

__version__ = "0.1.0"

from .hrs import HygieneRiskScore
from .scorer import HygienePrioScorer
from .metrics import precision_at_k, ndcg_at_k, oracle_gap

__all__ = [
    "HygieneRiskScore",
    "HygienePrioScorer",
    "precision_at_k",
    "ndcg_at_k",
    "oracle_gap",
]
