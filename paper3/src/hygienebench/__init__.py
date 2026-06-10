"""
HygieneBench v0.1 — Synthetic cyber-hygiene telemetry generator and benchmark.

Paper 3: A Reproducible Synthetic Benchmark for Cyber-Hygiene Anomaly Detection
Across Identity, Endpoint, and Patch Telemetry.

All data is synthetic. No employer, government, or production data is used or
referenced. All generation is seeded and deterministic.
"""

from hygienebench.generator import SyntheticHygieneGenerator, SyntheticHygieneDataset
from hygienebench.config import GeneratorConfig, PopulationConfig, ConditionConfig, AnomalyConfig
from hygienebench.schema import (
    FreshnessFlag, AssetCriticality, OsType, NetworkSegment,
    GroupType, RemediationAction, AccountAction, LogonType, AnomalyClass
)

__version__ = "0.2.0"
__all__ = [
    "SyntheticHygieneGenerator",
    "SyntheticHygieneDataset",
    "GeneratorConfig",
    "PopulationConfig",
    "ConditionConfig",
    "AnomalyConfig",
    "FreshnessFlag",
    "AssetCriticality",
    "OsType",
    "NetworkSegment",
    "GroupType",
    "RemediationAction",
    "AccountAction",
    "LogonType",
    "AnomalyClass",
]
