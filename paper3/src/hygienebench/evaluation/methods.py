"""
Detection methods M1–M8 for HygieneBench v0.1.

Each method implements:
  fit(X_train, feature_cols)  — fit on normal train-split data
  score(X)                    — return anomaly scores (higher = more anomalous)

M8 also requires the dataset_dir and task_id for graph construction.
"""

from __future__ import annotations
from typing import List, Optional
import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler


# ─────────────────────────────────────────────────────────────────────────────
# Base
# ─────────────────────────────────────────────────────────────────────────────
class BaseMethod:
    method_id: str = "base"
    requires_fit: bool = True

    def fit(self, X_train: np.ndarray, feature_cols: List[str]) -> None:
        pass

    def score(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError


def _scale(X_train: np.ndarray, X_test: np.ndarray):
    scaler = MinMaxScaler()
    X_tr = scaler.fit_transform(X_train)
    X_te = scaler.transform(X_test)
    return X_tr, X_te, scaler


# ─────────────────────────────────────────────────────────────────────────────
# M1 — Task-specific Rule Baseline
# ─────────────────────────────────────────────────────────────────────────────
class RuleBaseline(BaseMethod):
    method_id = "M1_rule"
    requires_fit = False

    def __init__(self, task_id: str):
        self.task_id = task_id

    def fit(self, X_train, feature_cols):
        self._cols = feature_cols

    def score(self, X: np.ndarray, feature_cols: Optional[List[str]] = None) -> np.ndarray:
        cols = feature_cols or self._cols
        df = pd.DataFrame(X, columns=cols)
        return self._rule_score(df).values

    def _rule_score(self, df: pd.DataFrame) -> pd.Series:
        s = pd.Series(0.0, index=df.index)
        t = self.task_id

        if t == "T1":
            s += np.where(df.get("days_since_last_logon", 0) > 90, 3.0, 0.0)
            s += np.where(df.get("days_since_last_logon", 0) > 30, 1.0, 0.0)
            s += np.where(df.get("privileged_group_count", 0) > 2, 1.0, 0.0)
            s += np.where(df.get("days_since_password_change", 0) > 180, 1.0, 0.0)
            s += np.where(df.get("mfa_enabled_int", 1) == 0, 1.0, 0.0)
            s += np.where(df.get("is_privileged_int", 0) == 1, 2.0, 0.0)
            s += df.get("freshness_score", 1.0).apply(lambda x: -1.0 if x < 0.3 else 0.0)

        elif t == "T2":
            s += np.where(df.get("is_privileged_group_int", 0) == 1, 4.0, 0.0)
            s += np.where(df.get("target_is_privileged", 0) == 0, 1.0, 0.0)  # non-priv added to priv group
            s += np.where(df.get("is_off_hours", 0) == 1, 1.0, 0.0)
            s += np.where(df.get("is_weekend", 0) == 1, 1.0, 0.0)

        elif t == "T3":
            s += np.where(df.get("open_kev", 0) >= 1, 4.0, 0.0)
            s += np.where(df.get("patch_compliance_score", 1.0) < 0.5, 2.0, 0.0)
            s += np.where(df.get("days_since_agent_heartbeat", 0) > 14, 2.0, 0.0)
            s += np.where(df.get("asset_crit_ord", 2) >= 4, 2.0, 0.0)
            s += np.where(df.get("max_kev_days_open", 0) > 30, 1.0, 0.0)
            s += np.where(df.get("primary_user_is_privileged", 0) == 1, 2.0, 0.0)

        elif t == "T4":
            s += np.where(df.get("agent_installed_int", 1) == 0, 4.0, 0.0)
            s += np.where(df.get("days_since_agent_heartbeat", 0) > 30, 3.0, 0.0)
            s += np.where(df.get("days_since_agent_heartbeat", 0) > 14, 2.0, 0.0)
            s += np.where(df.get("inventory_mismatch", 0) == 1, 3.0, 0.0)
            s += np.where(df.get("missing_source_count", 0) >= 1, 2.0, 0.0) * df.get("missing_source_count", 0)
            s += np.where(df.get("asset_crit_ord", 2) >= 3, 1.0, 0.0)

        elif t == "T5":
            s += np.where(df.get("open_kev", 0) >= 1, 4.0, 0.0)
            s += np.where(df.get("max_crit_days_open", 0) > 30, 3.0, 0.0)
            s += np.where(df.get("compliance", 1.0) < 0.5, 3.0, 0.0)
            s += np.where(df.get("crit_missing", 0) >= 3, 2.0, 0.0)
            s += np.where(df.get("max_rem_latency", 0) > 90, 2.0, 0.0)
            s += np.where(df.get("asset_crit_ord", 2) >= 4, 1.0, 0.0)

        elif t == "T6":
            s += np.where(df.get("dormant_days_at_react", 0) > 180, 4.0, 0.0)
            s += np.where(df.get("dormant_days_at_react", 0) > 90, 2.0, 0.0)
            s += np.where(df.get("was_reactivated", 0) >= 1, 1.0, 0.0)
            s += np.where(df.get("off_hours_rate", 0) > 0.5, 2.0, 0.0)
            s += np.where(df.get("cross_seg_rate", 0) > 0.2, 2.0, 0.0)
            s += np.where(df.get("is_privileged_int", 0) == 1, 2.0, 0.0)

        elif t == "T7":
            s += np.where(df.get("priv_adds", 0) >= 3, 5.0, 0.0)
            s += np.where(df.get("priv_adds", 0) >= 2, 2.0, 0.0)
            s += np.where(df.get("has_role_event", 1) == 0, 3.0, 0.0)
            s += np.where(df.get("priv_add_rate", 0) > 0, df.get("priv_add_rate", 0) * 10, 0.0)

        return pd.Series(s, index=df.index)


# ─────────────────────────────────────────────────────────────────────────────
# M2 — Hybrid Risk Scorer
# ─────────────────────────────────────────────────────────────────────────────
class HybridScorer(BaseMethod):
    method_id = "M2_hybrid"
    requires_fit = False

    def fit(self, X_train, feature_cols):
        self._cols = feature_cols

    def score(self, X: np.ndarray, feature_cols: Optional[List[str]] = None) -> np.ndarray:
        cols = feature_cols or self._cols
        df = pd.DataFrame(X, columns=cols)

        # Identity score (normalised inactivity + privilege weight)
        id_score = np.clip(df.get("days_since_last_logon", 0) / 365.0, 0, 1)
        id_score += np.clip(df.get("dormant_days_at_react", 0) / 365.0, 0, 1)
        id_score += df.get("priv_adds", 0) / 10.0
        id_score = id_score.clip(0, 1)

        # Endpoint score
        ep_score = 1.0 - df.get("compliance", pd.Series(1.0, index=df.index))
        agent_col = df["agent_installed_int"] if "agent_installed_int" in df.columns else pd.Series(1, index=df.index)
        ep_score += np.where(agent_col.fillna(1) == 0, 0.5, 0.0)
        ep_score += np.clip(df.get("days_since_agent_heartbeat", pd.Series(0, index=df.index)) / 30.0, 0, 1)
        ep_score = pd.Series(ep_score, index=df.index).clip(0, 1)

        # Vulnerability score
        vx_score = df.get("open_kev", pd.Series(0, index=df.index)).clip(0, 5) / 5.0
        vx_score += np.clip(df.get("max_crit_days_open", pd.Series(0, index=df.index)) / 120.0, 0, 1)
        vx_score += np.clip(df.get("kev_count", pd.Series(0, index=df.index)) / 5.0, 0, 1)
        vx_score = pd.Series(vx_score, index=df.index).clip(0, 1)

        # Freshness penalty (lower freshness → higher effective score)
        freshness_penalty = 1.0 - df.get("freshness_score", 1.0)

        # Weighted combination (equal weights; freshness multiplies uncertainty)
        combined = (id_score + ep_score + vx_score) / 3.0
        combined = combined * (1.0 + freshness_penalty * 0.3)

        return combined.fillna(0).values.astype(float)


# ─────────────────────────────────────────────────────────────────────────────
# M3 — Isolation Forest
# ─────────────────────────────────────────────────────────────────────────────
class IsolationForestMethod(BaseMethod):
    method_id = "M3_iforest"

    def __init__(self, seed: int, n_estimators: int = 200, contamination: float = 0.02):
        self.seed = seed
        self.n_estimators = n_estimators
        self.contamination = contamination
        self._scaler = MinMaxScaler()
        self._model = None

    def fit(self, X_train: np.ndarray, feature_cols: List[str]) -> None:
        X_s = self._scaler.fit_transform(np.nan_to_num(X_train))
        self._model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.seed,
        )
        self._model.fit(X_s)

    def score(self, X: np.ndarray, **_) -> np.ndarray:
        X_s = self._scaler.transform(np.nan_to_num(X))
        return -self._model.decision_function(X_s)  # higher = more anomalous


# ─────────────────────────────────────────────────────────────────────────────
# M4 — Local Outlier Factor
# ─────────────────────────────────────────────────────────────────────────────
class LOFMethod(BaseMethod):
    method_id = "M4_lof"

    def __init__(self, n_neighbors: int = 20):
        self.n_neighbors = n_neighbors
        self._scaler = MinMaxScaler()
        self._model = None

    def fit(self, X_train: np.ndarray, feature_cols: List[str]) -> None:
        X_s = self._scaler.fit_transform(np.nan_to_num(X_train))
        self._model = LocalOutlierFactor(
            n_neighbors=min(self.n_neighbors, len(X_train) - 1),
            novelty=True,
        )
        self._model.fit(X_s)

    def score(self, X: np.ndarray, **_) -> np.ndarray:
        X_s = self._scaler.transform(np.nan_to_num(X))
        return -self._model.decision_function(X_s)


# ─────────────────────────────────────────────────────────────────────────────
# M5 — One-Class SVM
# ─────────────────────────────────────────────────────────────────────────────
class OCSVMMethod(BaseMethod):
    method_id = "M5_ocsvm"

    def __init__(self, nu: float = 0.05):
        self.nu = nu
        self._scaler = MinMaxScaler()
        self._model = None

    def fit(self, X_train: np.ndarray, feature_cols: List[str]) -> None:
        X_s = self._scaler.fit_transform(np.nan_to_num(X_train))
        self._model = OneClassSVM(kernel="rbf", nu=self.nu, gamma="scale")
        self._model.fit(X_s)

    def score(self, X: np.ndarray, **_) -> np.ndarray:
        X_s = self._scaler.transform(np.nan_to_num(X))
        return -self._model.decision_function(X_s)


# ─────────────────────────────────────────────────────────────────────────────
# M6 — Linear Autoencoder (PCA-based reconstruction error)
# Documented as "Linear-AE" in results. No PyTorch required.
# ─────────────────────────────────────────────────────────────────────────────
class LinearAutoencoderMethod(BaseMethod):
    method_id = "M6_linearae"

    def __init__(self, latent_dim: int = 8):
        self.latent_dim = latent_dim
        self._scaler = MinMaxScaler()
        self._pca = None

    def fit(self, X_train: np.ndarray, feature_cols: List[str]) -> None:
        X_s = self._scaler.fit_transform(np.nan_to_num(X_train))
        n_comp = min(self.latent_dim, X_s.shape[1], X_s.shape[0] - 1)
        self._pca = PCA(n_components=n_comp)
        self._pca.fit(X_s)

    def score(self, X: np.ndarray, **_) -> np.ndarray:
        X_s = self._scaler.transform(np.nan_to_num(X))
        X_rec = self._pca.inverse_transform(self._pca.transform(X_s))
        # Per-sample reconstruction error (MSE)
        return np.mean((X_s - X_rec) ** 2, axis=1)


# ─────────────────────────────────────────────────────────────────────────────
# M7 — Temporal Z-Score (population z-score on key temporal signals)
# For HygieneBench v0.1: population-level z-score, not rolling (snapshot data).
# ─────────────────────────────────────────────────────────────────────────────
class TemporalZScoreMethod(BaseMethod):
    method_id = "M7_zscore"
    requires_fit = True

    # Features that carry temporal signal per task
    TEMPORAL_FEATURES = {
        "T1": ["days_since_last_logon", "days_since_password_change"],
        "T2": ["hour_of_day"],
        "T3": ["days_since_agent_heartbeat", "max_kev_days_open"],
        "T4": ["days_since_agent_heartbeat", "max_gap_days"],
        "T5": ["patch_lag", "max_crit_days_open", "max_rem_latency"],
        "T6": ["days_since_last_logon", "dormant_days_at_react"],
        "T7": ["priv_adds", "unique_days"],
    }

    def __init__(self, task_id: str):
        self.task_id = task_id
        self._means = None
        self._stds = None
        self._t_cols = None

    def fit(self, X_train: np.ndarray, feature_cols: List[str]) -> None:
        self._t_cols = [
            c for c in self.TEMPORAL_FEATURES.get(self.task_id, feature_cols)
            if c in feature_cols
        ]
        if not self._t_cols:
            self._t_cols = feature_cols[:2]
        idx = [feature_cols.index(c) for c in self._t_cols]
        X_t = np.nan_to_num(X_train[:, idx])
        self._means = X_t.mean(axis=0)
        self._stds = X_t.std(axis=0) + 1e-8
        self._idx = idx

    def score(self, X: np.ndarray, **_) -> np.ndarray:
        X_t = np.nan_to_num(X[:, self._idx])
        z = np.abs((X_t - self._means) / self._stds)
        return z.max(axis=1)  # max z-score across temporal features


# ─────────────────────────────────────────────────────────────────────────────
# M8 — Graph-Feature-Augmented Isolation Forest ("Graph-IF")
# Uses networkx to compute graph structural features per user,
# then combines with tabular features for Isolation Forest.
# Documented as "Graph-IF" in results — approximates DOMINANT-style approach.
# Applicable to: T2, T3, T7.
# ─────────────────────────────────────────────────────────────────────────────
class GraphIsolationForestMethod(BaseMethod):
    method_id = "M8_graphif"

    NA_TASKS = {"T4", "T5"}  # M8 excluded per EXPERIMENTAL_DESIGN_v0_1.md

    def __init__(self, task_id: str, dataset_dir: str, seed: int):
        self.task_id = task_id
        self.dataset_dir = dataset_dir
        self.seed = seed
        self._scaler = MinMaxScaler()
        self._model = None
        self._graph_features = None  # pre-computed graph features per entity

    def _build_graph_features(self) -> pd.DataFrame:
        """Build a networkx user-group graph and extract structural features per user."""
        import networkx as nx

        gme = pd.read_csv(f"{self.dataset_dir}/group_membership_events.csv", low_memory=False)
        groups = pd.read_csv(f"{self.dataset_dir}/groups.csv", low_memory=False)
        users = pd.read_csv(f"{self.dataset_dir}/users.csv", low_memory=False)

        priv_groups = set(groups[groups["is_privileged"]]["group_id"].tolist())
        all_user_ids = users["user_id"].tolist()

        G = nx.Graph()
        G.add_nodes_from([f"u:{u}" for u in all_user_ids])
        G.add_nodes_from([f"g:{g}" for g in groups["group_id"].tolist()])

        adds = gme[gme["action"] == "add"]
        for _, row in adds.iterrows():
            G.add_edge(f"u:{row['user_id']}", f"g:{row['group_id']}")

        records = []
        for uid in all_user_ids:
            node = f"u:{uid}"
            if node not in G:
                records.append({"entity_id": uid, "graph_degree": 0,
                                 "graph_priv_degree": 0, "graph_clustering": 0.0})
                continue
            deg = G.degree(node)
            priv_deg = sum(1 for nb in G.neighbors(node) if nb.replace("g:", "") in priv_groups)
            clust = nx.clustering(G, node)
            records.append({
                "entity_id": uid,
                "graph_degree": deg,
                "graph_priv_degree": priv_deg,
                "graph_clustering": clust,
            })
        return pd.DataFrame(records).set_index("entity_id")

    def fit(self, X_train: np.ndarray, feature_cols: List[str],
            entity_ids_train: Optional[list] = None) -> None:
        self._cols = feature_cols
        if self._graph_features is None:
            self._graph_features = self._build_graph_features()

        def _augment(X, eids):
            if eids is None or self._graph_features is None:
                return X
            gf = self._graph_features.reindex(eids).fillna(0).values
            return np.hstack([np.nan_to_num(X), gf])

        X_aug = _augment(X_train, entity_ids_train)
        X_s = self._scaler.fit_transform(X_aug)
        self._model = IsolationForest(n_estimators=200, contamination=0.02,
                                       random_state=self.seed)
        self._model.fit(X_s)
        self._entity_ids_train = entity_ids_train

    def score(self, X: np.ndarray, entity_ids: Optional[list] = None, **_) -> np.ndarray:
        if self._graph_features is not None and entity_ids is not None:
            gf = self._graph_features.reindex(entity_ids).fillna(0).values
            X_aug = np.hstack([np.nan_to_num(X), gf])
        else:
            X_aug = np.nan_to_num(X)
        X_s = self._scaler.transform(X_aug)
        return -self._model.decision_function(X_s)


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────
def get_method(method_id: str, task_id: str, seed: int = 42,
               dataset_dir: str = "") -> BaseMethod:
    m = {
        "M1_rule": lambda: RuleBaseline(task_id),
        "M2_hybrid": lambda: HybridScorer(),
        "M3_iforest": lambda: IsolationForestMethod(seed),
        "M4_lof": lambda: LOFMethod(),
        "M5_ocsvm": lambda: OCSVMMethod(),
        "M6_linearae": lambda: LinearAutoencoderMethod(),
        "M7_zscore": lambda: TemporalZScoreMethod(task_id),
        "M8_graphif": lambda: GraphIsolationForestMethod(task_id, dataset_dir, seed),
    }
    if method_id not in m:
        raise ValueError(f"Unknown method: {method_id}")
    return m[method_id]()


# Tasks where M8 is excluded per EXPERIMENTAL_DESIGN_v0_1.md
M8_EXCLUDED_TASKS = GraphIsolationForestMethod.NA_TASKS

ALL_METHOD_IDS = ["M1_rule", "M2_hybrid", "M3_iforest", "M4_lof",
                  "M5_ocsvm", "M6_linearae", "M7_zscore", "M8_graphif"]
