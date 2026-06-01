"""
EvaluationRunner — orchestrates all (condition, task, method, seed) runs.

Flow per run:
  1. TaskFeatureExtractor.extract() → features, labels, split
  2. Method.fit(X_train) → Method.score(X_test) → scores
  3. compute_metrics() → ap, pk, rk, fpb
  4. failure_flag() aggregated across seeds after all seeds for a config complete

Results are accumulated into a DataFrame and optionally saved as CSV + JSON manifests.
"""

from __future__ import annotations

import json
import os
import re
import traceback
import warnings
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from hygienebench.evaluation.features import TaskFeatureExtractor
from hygienebench.evaluation.methods import (
    get_method,
    ALL_METHOD_IDS,
    M8_EXCLUDED_TASKS,
)
from hygienebench.evaluation.metrics import (
    compute_metrics,
    failure_flag,
    rank_stability,
)

# k values per task (from TASK_SPECS.md §Evaluation budget)
TASK_K: Dict[str, int] = {
    "T1": 10,
    "T2": 20,
    "T3": 15,
    "T4": 20,
    "T5": 25,
    "T6": 10,
    "T7": 10,
}

# Rule baseline method per task (always M1_rule; M2_hybrid is a secondary baseline)
RULE_METHOD_ID = "M1_rule"


@dataclass
class RunRecord:
    condition_id: str
    task_id: str
    method_id: str
    seed: int
    ap: float
    pk: float
    rk: float
    fpb: float
    rule_ap: float
    rule_pk: float
    n_test: int
    n_test_pos: int
    k: int
    error: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EvaluationRunner:
    """
    Parameters
    ----------
    dataset_dirs : dict mapping condition_id → dataset_dir path
    seeds : list of integer seeds to evaluate over
    tasks : list of task IDs to run (default all T1-T7)
    methods : list of method IDs to run (default ALL_METHOD_IDS)
    results_dir : where to write outputs
    verbose : print progress to stdout
    """

    dataset_dirs: Dict[str, str]
    seeds: List[int] = field(default_factory=lambda: [42, 137, 2024])
    tasks: List[str] = field(default_factory=lambda: ["T1", "T2", "T3", "T4", "T5", "T6", "T7"])
    methods: List[str] = field(default_factory=lambda: list(ALL_METHOD_IDS))
    results_dir: str = "results"
    verbose: bool = True

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg)

    def _run_single(
        self,
        condition_id: str,
        dataset_dir: str,
        task_id: str,
        method_id: str,
        seed: int,
    ) -> RunRecord:
        """Execute one (condition, task, method, seed) run. Returns RunRecord."""
        k = TASK_K[task_id]
        ts = datetime.now(timezone.utc).isoformat()

        try:
            extractor = TaskFeatureExtractor(dataset_dir)
            entities_df, labels_series, feature_cols, split_series = extractor.extract(task_id, seed)

            if entities_df.empty or len(feature_cols) == 0:
                raise ValueError("Empty feature matrix after extraction")

            X = entities_df[feature_cols].values.astype(float)
            y = labels_series.values.astype(int)
            split = split_series.values

            train_mask = split == "train"
            test_mask = split == "test"

            # Fall back gracefully when splits are degenerate
            if train_mask.sum() == 0 or test_mask.sum() == 0:
                warnings.warn(f"Degenerate split for {condition_id}/{task_id}/{method_id}/seed={seed}")
                train_mask = np.ones(len(X), dtype=bool)
                test_mask = np.ones(len(X), dtype=bool)

            X_train, X_test = X[train_mask], X[test_mask]
            y_test = y[test_mask]

            # Replace NaN/Inf with column means (computed on train)
            col_means = np.nanmean(X_train, axis=0)
            col_means = np.where(np.isfinite(col_means), col_means, 0.0)
            for col_idx in range(X_train.shape[1]):
                X_train[:, col_idx] = np.where(
                    np.isfinite(X_train[:, col_idx]),
                    X_train[:, col_idx],
                    col_means[col_idx],
                )
                X_test[:, col_idx] = np.where(
                    np.isfinite(X_test[:, col_idx]),
                    X_test[:, col_idx],
                    col_means[col_idx],
                )

            # Fit and score target method
            method = get_method(method_id, task_id=task_id, seed=seed, dataset_dir=dataset_dir)
            method.fit(X_train, feature_cols)
            scores = method.score(X_test)

            # Fit and score rule baseline for delta computation
            rule_method = get_method(RULE_METHOD_ID, task_id=task_id, seed=seed, dataset_dir=dataset_dir)
            rule_method.fit(X_train, feature_cols)
            rule_scores = rule_method.score(X_test)

            metrics = compute_metrics(
                scores=scores,
                labels=y_test,
                k=k,
                rule_scores=rule_scores,
                rule_labels=y_test,
            )

            return RunRecord(
                condition_id=condition_id,
                task_id=task_id,
                method_id=method_id,
                seed=seed,
                ap=metrics["ap"],
                pk=metrics["pk"],
                rk=metrics["rk"],
                fpb=metrics["fpb"],
                rule_ap=metrics.get("rule_ap", float("nan")),
                rule_pk=metrics.get("rule_pk", float("nan")),
                n_test=int(len(y_test)),
                n_test_pos=int(np.sum(y_test)),
                k=k,
                error="",
                timestamp=ts,
            )

        except Exception as exc:
            tb = traceback.format_exc()
            self._log(f"  ERROR: {exc}")
            return RunRecord(
                condition_id=condition_id,
                task_id=task_id,
                method_id=method_id,
                seed=seed,
                ap=float("nan"),
                pk=float("nan"),
                rk=float("nan"),
                fpb=float("nan"),
                rule_ap=float("nan"),
                rule_pk=float("nan"),
                n_test=0,
                n_test_pos=0,
                k=k,
                error=str(exc)[:300],
                timestamp=ts,
            )

    def run(self) -> pd.DataFrame:
        """
        Execute all planned runs and return results DataFrame.

        Also writes:
          {results_dir}/primary_results.csv
          {results_dir}/failure_flags.csv
          {results_dir}/run_manifest.json
        """
        os.makedirs(self.results_dir, exist_ok=True)

        records: List[RunRecord] = []
        done = 0

        for condition_id, dataset_dir in self.dataset_dirs.items():
            self._log(f"\n=== Condition: {condition_id} | dir: {dataset_dir} ===")
            if not os.path.isdir(dataset_dir):
                self._log(f"  SKIP: dataset_dir not found: {dataset_dir}")
                continue

            # If condition_id encodes the seed (e.g. "c_base_seed42"), only run that seed
            seed_match = re.search(r"_seed(\d+)$", condition_id)
            if seed_match:
                effective_seeds = [int(seed_match.group(1))]
            else:
                effective_seeds = self.seeds

            for task_id in self.tasks:
                for method_id in self.methods:
                    # M8 is not applicable to T4 and T5
                    if method_id == "M8_graphif" and task_id in M8_EXCLUDED_TASKS:
                        continue

                    for seed in effective_seeds:
                        done += 1
                        self._log(
                            f"  [{done}] {condition_id} | {task_id} | {method_id} | seed={seed}"
                        )
                        rec = self._run_single(condition_id, dataset_dir, task_id, method_id, seed)
                        records.append(rec)

        df = pd.DataFrame([r.to_dict() for r in records])

        # Compute failure flags aggregated across seeds
        flag_rows = self._compute_failure_flags(df)
        flag_df = pd.DataFrame(flag_rows)

        # Compute rank stability per (condition, task, method)
        stability_rows = self._compute_rank_stability(df)
        stability_df = pd.DataFrame(stability_rows)

        # Save outputs
        results_csv = os.path.join(self.results_dir, "primary_results.csv")
        df.to_csv(results_csv, index=False)
        self._log(f"\nSaved results to {results_csv}")

        if not flag_df.empty:
            flags_csv = os.path.join(self.results_dir, "failure_flags.csv")
            flag_df.to_csv(flags_csv, index=False)
            self._log(f"Saved failure flags to {flags_csv}")

        if not stability_df.empty:
            stability_csv = os.path.join(self.results_dir, "rank_stability.csv")
            stability_df.to_csv(stability_csv, index=False)
            self._log(f"Saved rank stability to {stability_csv}")

        manifest = self._make_manifest(df, flag_df, stability_df)
        manifest_path = os.path.join(self.results_dir, "run_manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2, default=str)
        self._log(f"Saved run manifest to {manifest_path}")

        return df

    def _compute_failure_flags(self, df: pd.DataFrame) -> List[Dict]:
        rows = []
        if df.empty:
            return rows

        valid = df[df["error"] == ""].copy()
        if valid.empty:
            return rows

        for (condition_id, task_id, method_id), grp in valid.groupby(
            ["condition_id", "task_id", "method_id"]
        ):
            if method_id == RULE_METHOD_ID:
                continue  # skip flagging the baseline itself

            ap_list = grp["ap"].tolist()
            pk_list = grp["pk"].tolist()
            rule_ap_list = grp["rule_ap"].tolist()
            rule_pk_list = grp["rule_pk"].tolist()

            # Use per-seed rule values if available, else mean
            rule_ap_mean = float(np.nanmean(rule_ap_list))
            rule_pk_mean = float(np.nanmean(rule_pk_list))

            flag = failure_flag(
                ap_scores=ap_list,
                pk_scores=pk_list,
                rule_ap=rule_ap_mean,
                rule_pk=rule_pk_mean,
            )
            rows.append(
                {
                    "condition_id": condition_id,
                    "task_id": task_id,
                    "method_id": method_id,
                    "mean_ap": float(np.nanmean(ap_list)),
                    "mean_pk": float(np.nanmean(pk_list)),
                    "rule_ap": rule_ap_mean,
                    "rule_pk": rule_pk_mean,
                    "failure_flag": flag,
                    "n_seeds": len(grp),
                }
            )
        return rows

    def _compute_rank_stability(self, df: pd.DataFrame) -> List[Dict]:
        rows = []
        if df.empty:
            return rows

        valid = df[df["error"] == ""].copy()
        if valid.empty:
            return rows

        for (condition_id, task_id, method_id), grp in valid.groupby(
            ["condition_id", "task_id", "method_id"]
        ):
            ap_vals = grp["ap"].tolist()
            # We only have scalar metrics per seed; use AP as proxy rank signal
            scores_list = [np.array([v]) for v in ap_vals if not np.isnan(v)]
            if len(scores_list) < 2:
                tau = float("nan")
            else:
                # Use AP-across-seeds as simple stability proxy (scalar per seed)
                tau = float(np.std(ap_vals)) if len(ap_vals) > 1 else float("nan")
                # negative std so that low variance = high stability, express as 1-cv
                ap_mean = float(np.nanmean(ap_vals))
                if ap_mean > 0:
                    tau = 1.0 - (float(np.nanstd(ap_vals)) / ap_mean)
                else:
                    tau = float("nan")

            rows.append(
                {
                    "condition_id": condition_id,
                    "task_id": task_id,
                    "method_id": method_id,
                    "ap_stability_1_cv": tau,
                    "n_seeds": len(grp),
                }
            )
        return rows

    def _make_manifest(
        self,
        df: pd.DataFrame,
        flag_df: pd.DataFrame,
        stability_df: pd.DataFrame,
    ) -> Dict:
        total_runs = len(df)
        error_runs = int((df["error"] != "").sum()) if not df.empty else 0
        flagged = int(flag_df["failure_flag"].sum()) if not flag_df.empty else 0
        total_configs = len(flag_df)

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "hygienebench_version": "0.1",
            "total_runs": total_runs,
            "error_runs": error_runs,
            "success_runs": total_runs - error_runs,
            "conditions": list(self.dataset_dirs.keys()),
            "tasks": self.tasks,
            "methods": self.methods,
            "seeds": self.seeds,
            "total_method_task_condition_configs": total_configs,
            "failure_flagged_configs": flagged,
            "negative_result_rate": round(flagged / total_configs, 4) if total_configs > 0 else None,
            "negative_result_protocol": {
                "delta_ap": 0.05,
                "delta_pk": 0.05,
                "min_seed_fraction": "2/3",
                "interpretation": "flagged=True means ML did not outperform rule baseline by delta in >=2/3 seeds",
            },
        }
