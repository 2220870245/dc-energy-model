"""Dataset contract definitions for the energy model project."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


REQUIRED_COLUMNS: tuple[str, ...] = (
    "window_start",
    "cell",
    "pdu",
    "measured_power_util",
    "production_power_util",
    "instance_count",
    "collection_count",
    "machine_count",
    "total_cpu_usage",
    "avg_cpu_usage",
    "max_cpu_usage",
)

ID_COLUMNS: tuple[str, ...] = (
    "cell",
    "pdu",
    "window_start",
)

LABEL_COLUMNS: tuple[str, ...] = (
    "measured_power_util",
    "production_power_util",
)

BASE_FEATURE_COLUMNS: tuple[str, ...] = (
    "instance_count",
    "collection_count",
    "machine_count",
    "total_cpu_usage",
    "avg_cpu_usage",
    "max_cpu_usage",
)


@dataclass(frozen=True)
class SplitConfig:
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15

    def validate(self) -> None:
        total = self.train_ratio + self.val_ratio + self.test_ratio
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"Split ratios must sum to 1.0, got {total}")


@dataclass(frozen=True)
class DatasetContract:
    required_columns: Sequence[str] = REQUIRED_COLUMNS
    id_columns: Sequence[str] = ID_COLUMNS
    label_columns: Sequence[str] = LABEL_COLUMNS
    base_feature_columns: Sequence[str] = BASE_FEATURE_COLUMNS
