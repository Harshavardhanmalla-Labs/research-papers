"""
DatasetSplitter — assigns train/val/test splits per EXPERIMENTAL_DESIGN_v0_1.md.

Split: 60/20/20 by entity count, stratified by anomaly class.
Splits are assigned to anomaly_labels.split column.
Normal entities are also split (for unsupervised methods that train on normal data).
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from hygienebench.generator import SyntheticHygieneDataset


TRAIN_RATIO = 0.60
VAL_RATIO = 0.20
TEST_RATIO = 0.20


def assign_splits(ds: SyntheticHygieneDataset) -> SyntheticHygieneDataset:
    """
    Assigns 'train'/'val'/'test' to ds.anomaly_labels.split (stratified).
    Also adds a split column to ds.users for normal-entity splitting.
    Returns updated dataset.
    """
    seed = ds.config.seed
    rng = np.random.default_rng(seed)

    labels = ds.anomaly_labels.copy()

    if len(labels) > 0:
        # Stratified split per anomaly class
        labels["split"] = "unassigned"
        for cls in labels["anomaly_class"].unique():
            mask = labels["anomaly_class"] == cls
            idx = labels.index[mask].tolist()
            rng2 = np.random.default_rng(seed + abs(hash(cls)) % 10000)
            rng2.shuffle(idx)
            n = len(idx)
            n_train = max(1, int(n * TRAIN_RATIO))
            n_val = max(1, int(n * VAL_RATIO))
            for i, j in enumerate(idx):
                if i < n_train:
                    labels.at[j, "split"] = "train"
                elif i < n_train + n_val:
                    labels.at[j, "split"] = "val"
                else:
                    labels.at[j, "split"] = "test"

    # Split normal users (for methods that train on normal data)
    users = ds.users.copy()
    anomalous_user_ids = set()
    if len(labels) > 0:
        anomalous_user_ids = set(
            labels[labels["entity_type"] == "user"]["entity_id"].tolist()
        )

    normal_users = users[~users["user_id"].isin(anomalous_user_ids)].copy()
    idx_list = normal_users.index.tolist()
    rng.shuffle(idx_list)
    n = len(idx_list)
    n_train = int(n * TRAIN_RATIO)
    n_val = int(n * VAL_RATIO)

    users["split"] = "unassigned"
    for i, j in enumerate(idx_list):
        if i < n_train:
            users.at[j, "split"] = "train"
        elif i < n_train + n_val:
            users.at[j, "split"] = "val"
        else:
            users.at[j, "split"] = "test"

    for uid in anomalous_user_ids:
        umask = users["user_id"] == uid
        users.loc[umask, "split"] = "test"

    return SyntheticHygieneDataset(**{**ds.__dict__, "anomaly_labels": labels, "users": users})


def split_summary(ds: SyntheticHygieneDataset) -> dict:
    """Returns split counts for logging."""
    result = {}
    if "split" in ds.users.columns:
        result["users"] = ds.users["split"].value_counts().to_dict()
    if len(ds.anomaly_labels) > 0 and "split" in ds.anomaly_labels.columns:
        result["anomaly_labels"] = ds.anomaly_labels["split"].value_counts().to_dict()
    return result
