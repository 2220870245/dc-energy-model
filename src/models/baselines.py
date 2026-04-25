"""Baseline model registry for the energy model project."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge


@dataclass
class BaselineSpec:
    name: str
    feature_columns: list[str]


class PersistenceBaseline:
    def fit(self, x: np.ndarray, y: np.ndarray) -> "PersistenceBaseline":
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        return x[:, 0]


class MovingAverageBaseline:
    def fit(self, x: np.ndarray, y: np.ndarray) -> "MovingAverageBaseline":
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        return np.mean(x[:, :2], axis=1)


class CpuHeuristicBaseline:
    def fit(self, x: np.ndarray, y: np.ndarray) -> "CpuHeuristicBaseline":
        cpu = x[:, 0]
        design = np.stack([np.ones_like(cpu), cpu], axis=1)
        beta, *_ = np.linalg.lstsq(design, y, rcond=None)
        self.bias_ = float(beta[0])
        self.weight_ = float(beta[1])
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        return self.bias_ + self.weight_ * x[:, 0]


def build_model(name: str):
    if name == "persistence":
        return PersistenceBaseline()
    if name == "moving_average":
        return MovingAverageBaseline()
    if name == "linear_regression":
        return LinearRegression()
    if name == "ridge":
        return Ridge(alpha=1.0)
    if name == "cpu_heuristic":
        return CpuHeuristicBaseline()
    if name == "random_forest":
        return RandomForestRegressor(
            n_estimators=200,
            max_depth=8,
            random_state=42,
            n_jobs=1,
        )
    raise ValueError(f"Unknown baseline model: {name}")


def default_feature_sets() -> dict[str, list[str]]:
    return {
        "persistence": ["prev_measured_power_util"],
        "moving_average": ["prev_measured_power_util", "prev_total_cpu_usage"],
        "linear_regression": [
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
        ],
        "ridge": [
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
        ],
        "cpu_heuristic": ["total_cpu_usage"],
        "random_forest": [
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
        ],
    }
