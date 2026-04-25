"""Sequence dataset utilities for deep learning experiments."""

from __future__ import annotations

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


def build_sequence_frame(
    frame: pd.DataFrame,
    feature_columns: list[str],
    label_column: str,
    context_length: int,
) -> tuple[np.ndarray, np.ndarray]:
    if context_length < 1:
        raise ValueError("context_length must be >= 1")

    required = ["cell", "pdu", "window_start", label_column, *feature_columns]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing sequence columns: {missing}")

    x_batches: list[np.ndarray] = []
    y_batches: list[float] = []

    ordered = frame.sort_values(["cell", "pdu", "window_start"]).reset_index(drop=True)
    for _, group in ordered.groupby(["cell", "pdu"], sort=False):
        values = group[feature_columns].to_numpy(dtype=np.float32)
        targets = group[label_column].to_numpy(dtype=np.float32)
        if len(group) <= context_length:
            continue
        for idx in range(context_length, len(group)):
            x_batches.append(values[idx - context_length : idx])
            y_batches.append(float(targets[idx]))

    if not x_batches:
        raise ValueError("No sequence samples were created. Check split size and context_length.")

    return np.stack(x_batches), np.asarray(y_batches, dtype=np.float32)


class PDUPowerSequenceDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    def __init__(
        self,
        frame: pd.DataFrame,
        feature_columns: list[str],
        label_column: str,
        context_length: int,
    ) -> None:
        features, targets = build_sequence_frame(
            frame=frame,
            feature_columns=feature_columns,
            label_column=label_column,
            context_length=context_length,
        )
        self.features = torch.from_numpy(features)
        self.targets = torch.from_numpy(targets).unsqueeze(-1)

    def __len__(self) -> int:
        return int(self.features.shape[0])

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.features[index], self.targets[index]
