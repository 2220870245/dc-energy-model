"""Quality checks for the PDU training dataset."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


@dataclass(frozen=True)
class QualitySummary:
    row_count: int
    duplicate_rows: int
    min_label: float
    max_label: float
    null_cells: int
    null_pdus: int
    null_windows: int
    missing_rate_by_column: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def summarize_quality(frame: pd.DataFrame, label_column: str) -> QualitySummary:
    duplicate_rows = int(frame.duplicated(subset=["cell", "pdu", "window_start"]).sum())
    missing_rate = {
        column: float(frame[column].isna().mean())
        for column in frame.columns
    }
    return QualitySummary(
        row_count=int(len(frame)),
        duplicate_rows=duplicate_rows,
        min_label=float(frame[label_column].min()),
        max_label=float(frame[label_column].max()),
        null_cells=int(frame["cell"].isna().sum()),
        null_pdus=int(frame["pdu"].isna().sum()),
        null_windows=int(frame["window_start"].isna().sum()),
        missing_rate_by_column=missing_rate,
    )


def assert_no_time_leakage(train_end: pd.Timestamp, val_start: pd.Timestamp, test_start: pd.Timestamp) -> None:
    if not (train_end < val_start <= test_start):
        raise ValueError(
            "Time leakage detected: expected train_end < val_start <= test_start"
        )
