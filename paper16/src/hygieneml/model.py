"""
Paper 16: cyber-hygiene anomaly detection.

Generates a synthetic 1500-host fleet with a 12-dimensional hygiene telemetry vector
(four features in each of three channels: Active Directory, endpoint, patch), injects
single-dimension or cross-dimensional anomalies, scores every host with rule baselines and
multivariate detectors, and computes average precision. All constants are pre-registered in
PAPER16_PROTOCOL.md and fixed; no hyperparameter is tuned on any seed.
"""

from __future__ import annotations

import warnings

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.metrics import average_precision_score

warnings.filterwarnings("ignore")

# Pre-registered constants (PAPER16_PROTOCOL.md sections 3 and 4).
N_HOSTS = 1500
N_CHANNELS = 3                  # AD, endpoint, patch
FEATS_PER_CHANNEL = 4
N_FEATURES = N_CHANNELS * FEATS_PER_CHANNEL   # 12
ANOMALY_PREV = 0.08
SDA_SHIFT = 3.0                 # single-dimension anomaly shift (sigma)
WITHIN_CHANNEL_CORR = 0.70      # within-channel correlation for normal hosts;
                                # cross-dimensional anomalies violate this structure
RULE_Z = 2.5                    # Rule-Count exceedance threshold
EVALUATION_SEEDS = list(range(700, 725))
CHANNELS = ["AD", "endpoint", "patch"]
DETECTORS = ["Rule-Max", "Rule-Count", "Mahalanobis",
             "IsolationForest", "OneClassSVM", "LocalOutlierFactor"]
CONDITIONS = ["SDA", "CDA", "Mixed"]


def _channel_cov() -> np.ndarray:
    """Block-diagonal covariance: mild correlation within each channel, independent across."""
    cov = np.eye(N_FEATURES)
    for ch in range(N_CHANNELS):
        s = ch * FEATS_PER_CHANNEL
        for i in range(FEATS_PER_CHANNEL):
            for j in range(FEATS_PER_CHANNEL):
                if i != j:
                    cov[s + i, s + j] = WITHIN_CHANNEL_CORR
    return cov


def generate_fleet(seed: int, condition: str):
    """Return (X, y): feature matrix (N_HOSTS, 12) and binary anomaly labels."""
    rng = np.random.default_rng((seed, hash(condition) % 9973))
    cov = _channel_cov()
    X = rng.multivariate_normal(np.zeros(N_FEATURES), cov, size=N_HOSTS)
    y = np.zeros(N_HOSTS, dtype=int)

    n_anom = int(round(ANOMALY_PREV * N_HOSTS))
    idx = rng.choice(N_HOSTS, size=n_anom, replace=False)
    y[idx] = 1

    for h in idx:
        if condition == "SDA":
            typ = "SDA"
        elif condition == "CDA":
            typ = "CDA"
        else:  # Mixed: 50/50
            typ = "SDA" if rng.random() < 0.5 else "CDA"

        if typ == "SDA":
            ch = rng.integers(0, N_CHANNELS)
            s = ch * FEATS_PER_CHANNEL
            X[h, s:s + FEATS_PER_CHANNEL] += rng.normal(SDA_SHIFT, 0.5, FEATS_PER_CHANNEL)
        else:  # CDA: correlation-structure violation. Same per-feature marginal as normal
               # hosts (standard normal), but features drawn independently, breaking the
               # within-channel correlation. Individually unremarkable, jointly anomalous.
            X[h, :] = rng.standard_normal(N_FEATURES)
    return X, y


# ---------------------------------------------------------------------------
# Detectors (each returns a per-host anomaly score; higher = more anomalous)
# ---------------------------------------------------------------------------

def _robust_z(X: np.ndarray) -> np.ndarray:
    med = np.median(X, axis=0)
    mad = np.median(np.abs(X - med), axis=0) * 1.4826 + 1e-9
    return (X - med) / mad


def score_detector(name: str, X: np.ndarray, seed: int) -> np.ndarray:
    if name == "Rule-Max":
        return np.max(np.abs(_robust_z(X)), axis=1)
    if name == "Rule-Count":
        return np.sum(np.abs(_robust_z(X)) > RULE_Z, axis=1).astype(float)
    if name == "Mahalanobis":
        mu = X.mean(axis=0)
        cov = np.cov(X, rowvar=False) + 1e-6 * np.eye(X.shape[1])
        inv = np.linalg.inv(cov)
        d = X - mu
        return np.einsum("ij,jk,ik->i", d, inv, d)
    if name == "IsolationForest":
        m = IsolationForest(n_estimators=200, random_state=seed, contamination="auto")
        m.fit(X)
        return -m.score_samples(X)
    if name == "OneClassSVM":
        m = OneClassSVM(kernel="rbf", nu=0.1, gamma="scale")
        m.fit(X)
        return -m.decision_function(X)
    if name == "LocalOutlierFactor":
        m = LocalOutlierFactor(n_neighbors=20)
        m.fit_predict(X)
        return -m.negative_outlier_factor_
    raise ValueError(name)


def evaluate_seed(seed: int) -> list[dict]:
    """Average precision and precision@anomaly-count for each (condition, detector)."""
    rows = []
    for cond in CONDITIONS:
        X, y = generate_fleet(seed, cond)
        n_pos = int(y.sum())
        for det in DETECTORS:
            s = score_detector(det, X, seed)
            ap = average_precision_score(y, s)
            order = np.argsort(s)[::-1][:n_pos]
            p_at_k = float(y[order].sum()) / n_pos
            rows.append({"seed": seed, "condition": cond, "detector": det,
                         "n_pos": n_pos, "ap": round(float(ap), 4),
                         "p_at_k": round(p_at_k, 4)})
    return rows
