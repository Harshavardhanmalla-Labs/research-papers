"""
Asset Context layer for Paper 11 (CAP-G).

Extends the EEHDA government fleet with three pre-registered context attributes
(PAPER11_PROTOCOL.md §4) and computes the Asset Context Score (ACS).

All category mixes are structural priors grounded in public guidance
(NIST FIPS 199 / SP 800-60, CISA BOD 22-01/23-01, CJIS Security Policy v5.9).
No employer or operational data is used.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Pre-registered category value maps + fleet-share priors (§4)
# ---------------------------------------------------------------------------

CRITICALITY_VALUES = {
    "MISSION_CRITICAL": 1.00,
    "HIGH": 0.70,
    "MEDIUM": 0.40,
    "LOW": 0.15,
}
CRITICALITY_SHARES = {
    "MISSION_CRITICAL": 0.05,
    "HIGH": 0.20,
    "MEDIUM": 0.50,
    "LOW": 0.25,
}

ZONE_VALUES = {
    "INTERNET_FACING": 1.00,
    "DMZ": 0.75,
    "INTERNAL": 0.40,
    "ISOLATED": 0.10,
}
ZONE_SHARES = {
    "INTERNET_FACING": 0.08,
    "DMZ": 0.12,
    "INTERNAL": 0.65,
    "ISOLATED": 0.15,
}

SENSITIVITY_VALUES = {
    "CJIS": 1.00,
    "PII_CUI": 0.60,
    "PUBLIC": 0.20,
}
SENSITIVITY_SHARES = {
    "CJIS": 0.15,
    "PII_CUI": 0.45,
    "PUBLIC": 0.40,
}


@dataclass
class ContextWeights:
    """Pre-registered ACS dimension weights (criticality-dominant; §4.4)."""
    crit: float = 0.5
    zone: float = 0.3
    sens: float = 0.2

    def __post_init__(self) -> None:
        for name, val in [("crit", self.crit), ("zone", self.zone), ("sens", self.sens)]:
            if val < 0:
                raise ValueError(f"ACS weight '{name}' must be non-negative, got {val}")


def _sample_categorical(
    rng: np.random.Generator, n: int, shares: dict[str, float]
) -> np.ndarray:
    cats = list(shares.keys())
    probs = np.array([shares[c] for c in cats], dtype=float)
    probs = probs / probs.sum()
    return rng.choice(cats, size=n, p=probs)


def assign_context(
    computers: pd.DataFrame,
    seed: int,
    *,
    homogeneous: bool = False,
    host_id_col: str = "computer_id",
) -> pd.DataFrame:
    """
    Assign the three context attributes (§4) to each host and return a copy of
    ``computers`` with added columns:
        asset_criticality, network_zone, data_sensitivity   (categorical)
        crit_value, zone_value, sens_value                  (normalized [0,1])

    Deterministic from ``seed`` (independent stream from CVE attributes, no leakage).

    Parameters
    ----------
    homogeneous : bool
        If True, every host is assigned the SAME context (MEDIUM / INTERNAL / PII_CUI).
        Used for the H3 mechanism control (PAPER11_PROTOCOL.md §3, RQ3).
    """
    df = computers.copy()
    n = len(df)
    # Dedicated RNG stream for context (offset from any CVE/fleet stream).
    rng = np.random.default_rng((seed, 0xC047E47))  # "CONTEXT" stream tag

    if homogeneous:
        crit = np.full(n, "MEDIUM")
        zone = np.full(n, "INTERNAL")
        sens = np.full(n, "PII_CUI")
    else:
        crit = _sample_categorical(rng, n, CRITICALITY_SHARES)
        zone = _sample_categorical(rng, n, ZONE_SHARES)
        sens = _sample_categorical(rng, n, SENSITIVITY_SHARES)

    df["asset_criticality"] = crit
    df["network_zone"] = zone
    df["data_sensitivity"] = sens
    df["crit_value"] = np.vectorize(CRITICALITY_VALUES.get)(crit).astype(float)
    df["zone_value"] = np.vectorize(ZONE_VALUES.get)(zone).astype(float)
    df["sens_value"] = np.vectorize(SENSITIVITY_VALUES.get)(sens).astype(float)
    return df


def asset_context_score(
    computers_ctx: pd.DataFrame,
    weights: Optional[ContextWeights] = None,
    *,
    aggregation: str = "weighted",
    host_id_col: str = "computer_id",
) -> pd.Series:
    """
    ACS(h) over hosts. Returns a Series indexed by host_id in [0, 1].

    aggregation:
        "weighted" : c1·crit + c2·zone + c3·sens          (primary, §4.4)
        "hwm"      : max(crit, zone, sens)                 (FIPS 199 high-water-mark)
    """
    w = weights or ContextWeights()
    df = computers_ctx
    crit = df["crit_value"].to_numpy(dtype=float)
    zone = df["zone_value"].to_numpy(dtype=float)
    sens = df["sens_value"].to_numpy(dtype=float)

    if aggregation == "hwm":
        acs = np.maximum.reduce([crit, zone, sens])
    elif aggregation == "weighted":
        denom = w.crit + w.zone + w.sens
        denom = denom if denom > 0 else 1.0
        acs = (w.crit * crit + w.zone * zone + w.sens * sens) / denom
    else:
        raise ValueError(f"unknown aggregation '{aggregation}'")

    return pd.Series(
        np.clip(acs, 0.0, 1.0),
        index=df[host_id_col].to_numpy(),
        name="ACS",
    )
