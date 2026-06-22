"""
Paper 12: compliance-as-code exposure model.

A catalog of 200 NIST-800-53-style control instances drifts out of compliance as a Poisson
process; each drift is detected either at the next periodic assessment or, for automatable
controls under continuous monitoring, within a one-day collection cadence, and remediated a
fixed time later. We compute mean time to detect and compliance exposure (control-days out of
compliance) under periodic and continuous regimes. All constants are pre-registered in
PAPER12_PROTOCOL.md and fixed.
"""

from __future__ import annotations

import numpy as np

# Pre-registered constants (PAPER12_PROTOCOL.md section 3).
N_CONTROLS = 200
HORIZON_DAYS = 730
MTTR_DAYS = 7
CONTINUOUS_CADENCE = 1
FRAC_HIGH_DRIFT = 0.30
HIGH_DRIFT_RATE = 6.0       # drift events per year
LOW_DRIFT_RATE = 0.5
AUTO_PROB_HIGH = 0.85       # automatable probability for high-drift technical controls
AUTO_PROB_LOW = 0.35
EVALUATION_SEEDS = list(range(800, 825))
ANNUAL, QUARTERLY = 365, 90


def generate_catalog(seed: int):
    """Return arrays (lam_per_day, automatable, is_high_drift) for the control catalog."""
    rng = np.random.default_rng((seed, 12))
    is_high = rng.random(N_CONTROLS) < FRAC_HIGH_DRIFT
    lam_year = np.where(is_high, HIGH_DRIFT_RATE, LOW_DRIFT_RATE)
    auto_p = np.where(is_high, AUTO_PROB_HIGH, AUTO_PROB_LOW)
    automatable = rng.random(N_CONTROLS) < auto_p
    return lam_year / 365.0, automatable, is_high, rng


def _drift_times(lam_per_day: float, rng: np.random.Generator) -> np.ndarray:
    """Poisson drift event times within the horizon (sorted)."""
    if lam_per_day <= 0:
        return np.array([])
    times, t = [], 0.0
    while True:
        t += rng.exponential(1.0 / lam_per_day)
        if t >= HORIZON_DAYS:
            break
        times.append(t)
    return np.array(times)


def _periodic_detect(d: float, T: int) -> float:
    """Next assessment at a multiple of T at or after the drift time d."""
    k = np.ceil(d / T)
    return k * T


def _process_control(drift_times: np.ndarray, detect, mttr: float):
    """Walk a control's drift timeline; return (noncompliant_days, [detection_latencies])."""
    noncompliant = 0.0
    t_clear = 0.0
    latencies = []
    for d in drift_times:
        if d < t_clear:
            continue                      # already non-compliant; absorbed
        det = detect(d)
        remediated = det + mttr
        noncompliant += (remediated - d)
        latencies.append(det - d)
        t_clear = remediated
    return noncompliant, latencies


def evaluate_seed(seed: int) -> dict:
    lam, automatable, is_high, rng = generate_catalog(seed)
    # Pre-generate each control's drift timeline once; reuse across regimes for a fair comparison.
    drift = [_drift_times(lam[i], np.random.default_rng((seed, i, 99))) for i in range(N_CONTROLS)]

    def regime(T: int, continuous: bool, auto_subset=None):
        """Total exposure, MTTD (all and automatable-only), and automatable-share."""
        exposure = 0.0
        exposure_auto = 0.0
        all_lat, auto_lat = [], []
        for i in range(N_CONTROLS):
            use_continuous = continuous and (automatable[i] if auto_subset is None else auto_subset[i])
            if use_continuous:
                detect = lambda d: d + CONTINUOUS_CADENCE
            else:
                detect = lambda d, T=T: _periodic_detect(d, T)
            nc, lat = _process_control(drift[i], detect, MTTR_DAYS)
            exposure += nc
            all_lat.extend(lat)
            if automatable[i]:
                exposure_auto += nc
                auto_lat.extend(lat)
        return {"exposure": exposure, "exposure_auto": exposure_auto,
                "mttd": float(np.mean(all_lat)) if all_lat else 0.0,
                "mttd_auto": float(np.mean(auto_lat)) if auto_lat else 0.0}

    per_annual = regime(ANNUAL, continuous=False)
    per_quarter = regime(QUARTERLY, continuous=False)
    cont_annual = regime(ANNUAL, continuous=True)
    cont_quarter = regime(QUARTERLY, continuous=True)

    # H2 ceiling: automatable share of baseline (annual periodic) exposure.
    auto_share = per_annual["exposure_auto"] / per_annual["exposure"] if per_annual["exposure"] else 0.0

    # H4: automate only the top-drift quartile.
    thr = np.quantile(lam, 0.75)
    top_quartile = (lam >= thr)
    cont_top = regime(ANNUAL, continuous=True, auto_subset=(top_quartile & automatable))

    def reduction(base, cont):
        return (base["exposure"] - cont["exposure"]) / base["exposure"] if base["exposure"] else 0.0

    red_all_annual = reduction(per_annual, cont_annual)
    red_top_annual = reduction(per_annual, cont_top)

    days_saved_annual = per_annual["exposure"] - cont_annual["exposure"]
    days_saved_quarter = per_quarter["exposure"] - cont_quarter["exposure"]

    return {
        "seed": seed,
        "automatable_fraction": float(automatable.mean()),
        # MTTD on automatable controls (where continuous monitoring applies).
        "mttd_auto_annual": per_annual["mttd_auto"],
        "mttd_auto_continuous": cont_annual["mttd_auto"],
        "mttd_auto_ratio": (per_annual["mttd_auto"] / cont_annual["mttd_auto"])
        if cont_annual["mttd_auto"] > 0 else 0.0,
        # MTTD over all controls (bounded by automatability).
        "mttd_all_annual": per_annual["mttd"],
        "mttd_all_continuous": cont_annual["mttd"],
        "exposure_annual": per_annual["exposure"],
        "exposure_quarter": per_quarter["exposure"],
        "reduction_vs_annual": red_all_annual,
        "reduction_vs_quarter": reduction(per_quarter, cont_quarter),
        "automatable_exposure_share": auto_share,
        "ceiling_gap": red_all_annual - auto_share,
        "days_saved_vs_annual": days_saved_annual,
        "days_saved_vs_quarter": days_saved_quarter,
        "reduction_top_quartile": red_top_annual,
        "top_quartile_capture": (red_top_annual / red_all_annual) if red_all_annual > 0 else 0.0,
    }
