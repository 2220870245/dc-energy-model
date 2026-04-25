"""Sequence dataset utilities for deep learning experiments."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


DEFAULT_SEQUENCE_FEATURES: tuple[str, ...] = (
    "instance_count",
    "collection_count",
    "machine_count",
    "total_cpu_usage",
    "avg_cpu_usage",
    "max_cpu_usage",
    "hour",
    "day_of_week",
    "is_weekend",
    "prev_measured_power_util",
    "prev_total_cpu_usage",
)


def _prepare_ordered_sequence_frame(
    frame: pd.DataFrame,
    required_columns: list[str],
    history_frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing sequence columns: {missing}")

    target_frame = frame.copy()
    target_frame["_is_target"] = True
    if history_frame is not None:
        history_missing = [column for column in required_columns if column not in history_frame.columns]
        if history_missing:
            raise ValueError(f"Missing history sequence columns: {history_missing}")
        history_only = history_frame.copy()
        history_only["_is_target"] = False
        combined = pd.concat([history_only, target_frame], ignore_index=True)
    else:
        combined = target_frame
    return combined.sort_values(["cell", "pdu", "window_start"]).reset_index(drop=True)


def build_sequence_frame(
    frame: pd.DataFrame,
    feature_columns: list[str],
    label_column: str,
    context_length: int,
    history_frame: pd.DataFrame | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    if context_length < 1:
        raise ValueError("context_length must be >= 1")

    required = ["cell", "pdu", "window_start", label_column, *feature_columns]
    x_batches: list[np.ndarray] = []
    y_batches: list[float] = []

    ordered = _prepare_ordered_sequence_frame(
        frame=frame,
        required_columns=required,
        history_frame=history_frame,
    )
    for _, group in ordered.groupby(["cell", "pdu"], sort=False):
        values = group[feature_columns].to_numpy(dtype=np.float32)
        targets = group[label_column].to_numpy(dtype=np.float32)
        target_mask = group["_is_target"].to_numpy(dtype=bool)
        for idx in range(context_length, len(group)):
            if not target_mask[idx]:
                continue
            x_batches.append(values[idx - context_length : idx])
            y_batches.append(float(targets[idx]))

    if not x_batches:
        raise ValueError("No sequence samples were created. Check split size and context_length.")

    return np.stack(x_batches), np.asarray(y_batches, dtype=np.float32)


def collect_sequence_targets(
    frame: pd.DataFrame,
    value_column: str,
    context_length: int,
    history_frame: pd.DataFrame | None = None,
) -> np.ndarray:
    if context_length < 1:
        raise ValueError("context_length must be >= 1")

    ordered = _prepare_ordered_sequence_frame(
        frame=frame,
        required_columns=["cell", "pdu", "window_start", value_column],
        history_frame=history_frame,
    )
    values_out: list[float] = []
    for _, group in ordered.groupby(["cell", "pdu"], sort=False):
        target_mask = group["_is_target"].to_numpy(dtype=bool)
        column_values = group[value_column].to_numpy(dtype=np.float32)
        for idx in range(context_length, len(group)):
            if not target_mask[idx]:
                continue
            values_out.append(float(column_values[idx]))

    if not values_out:
        raise ValueError("No sequence targets were collected. Check split size and context_length.")
    return np.asarray(values_out, dtype=np.float32)


@dataclass(frozen=True)
class SequenceStandardizer:
    feature_mean: np.ndarray
    feature_std: np.ndarray
    target_mean: float
    target_std: float

    @classmethod
    def fit(
        cls,
        frame: pd.DataFrame,
        feature_columns: list[str],
        label_column: str,
        context_length: int,
    ) -> "SequenceStandardizer":
        features, targets = build_sequence_frame(
            frame=frame,
            feature_columns=feature_columns,
            label_column=label_column,
            context_length=context_length,
        )
        feature_mean = features.mean(axis=(0, 1))
        feature_std = features.std(axis=(0, 1))
        feature_std = np.where(feature_std < 1e-6, 1.0, feature_std)
        target_mean = float(targets.mean())
        target_std = float(targets.std())
        if target_std < 1e-6:
            target_std = 1.0
        return cls(
            feature_mean=feature_mean.astype(np.float32),
            feature_std=feature_std.astype(np.float32),
            target_mean=target_mean,
            target_std=target_std,
        )

    def transform_features(self, features: np.ndarray) -> np.ndarray:
        return ((features - self.feature_mean) / self.feature_std).astype(np.float32)

    def transform_targets(self, targets: np.ndarray) -> np.ndarray:
        return ((targets - self.target_mean) / self.target_std).astype(np.float32)

    def inverse_targets(self, targets: np.ndarray) -> np.ndarray:
        return (targets * self.target_std + self.target_mean).astype(np.float32)


class PDUPowerSequenceDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    def __init__(
        self,
        frame: pd.DataFrame,
        feature_columns: list[str],
        label_column: str,
        context_length: int,
        history_frame: pd.DataFrame | None = None,
        standardizer: SequenceStandardizer | None = None,
    ) -> None:
        features, targets = build_sequence_frame(
            frame=frame,
            feature_columns=feature_columns,
            label_column=label_column,
            context_length=context_length,
            history_frame=history_frame,
        )
        if standardizer is not None:
            features = standardizer.transform_features(features)
            targets = standardizer.transform_targets(targets)
        self.features = torch.from_numpy(features)
        self.targets = torch.from_numpy(targets).unsqueeze(-1)
        self.sample_count = int(self.features.shape[0])

    def __len__(self) -> int:
        return int(self.features.shape[0])

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.features[index], self.targets[index]
