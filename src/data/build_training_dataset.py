"""Build a versioned training dataset from exported BigQuery results."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from dataset_contract import BASE_FEATURE_COLUMNS, REQUIRED_COLUMNS, SplitConfig
from quality_checks import assert_no_time_leakage, summarize_quality


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to input parquet or csv file")
    parser.add_argument("--output-dir", required=True, help="Directory for processed dataset outputs")
    parser.add_argument("--report-path", required=True, help="Markdown path for the quality report")
    parser.add_argument("--version", default="v1", help="Dataset version label")
    parser.add_argument("--label", default="measured_power_util", help="Target label column")
    parser.add_argument(
        "--split-mode",
        choices=["chronological", "full_only"],
        default="chronological",
        help="Whether to build train/val/test splits or keep the whole table as one holdout dataset",
    )
    return parser.parse_args()


def load_frame(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


def validate_columns(frame: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def build_features(frame: pd.DataFrame, label_column: str) -> pd.DataFrame:
    built = frame.copy()
    built["window_start"] = pd.to_datetime(built["window_start"], utc=True)
    built = built.sort_values(["cell", "pdu", "window_start"]).reset_index(drop=True)

    built["hour"] = built["window_start"].dt.hour
    built["day_of_week"] = built["window_start"].dt.dayofweek
    built["is_weekend"] = built["day_of_week"].isin([5, 6]).astype(int)
    minute_of_day = built["window_start"].dt.hour * 60 + built["window_start"].dt.minute
    built["hour_sin"] = np.sin(2.0 * math.pi * minute_of_day / 1440.0)
    built["hour_cos"] = np.cos(2.0 * math.pi * minute_of_day / 1440.0)
    built["day_of_week_sin"] = np.sin(2.0 * math.pi * built["day_of_week"] / 7.0)
    built["day_of_week_cos"] = np.cos(2.0 * math.pi * built["day_of_week"] / 7.0)
    built["prev_measured_power_util"] = built.groupby(["cell", "pdu"])[label_column].shift(1)
    built["prev_production_power_util"] = built.groupby(["cell", "pdu"])["production_power_util"].shift(1)
    built["prev_total_cpu_usage"] = built.groupby(["cell", "pdu"])["total_cpu_usage"].shift(1)
    built["delta_total_cpu_usage"] = built["total_cpu_usage"] - built["prev_total_cpu_usage"]

    machine_count = built["machine_count"].replace(0, np.nan)
    instance_count = built["instance_count"].replace(0, np.nan)
    built["cpu_per_machine"] = built["total_cpu_usage"] / machine_count
    built["cpu_per_instance"] = built["total_cpu_usage"] / instance_count
    built["cpu_spread"] = built["max_cpu_usage"] - built["avg_cpu_usage"]

    numeric_fill_columns = list(BASE_FEATURE_COLUMNS) + [
        "prev_measured_power_util",
        "prev_production_power_util",
        "prev_total_cpu_usage",
        "delta_total_cpu_usage",
        "cpu_per_machine",
        "cpu_per_instance",
        "cpu_spread",
        "hour_sin",
        "hour_cos",
        "day_of_week_sin",
        "day_of_week_cos",
    ]
    for column in numeric_fill_columns:
        if column in built.columns:
            built[column] = built[column].fillna(0.0)

    return built


def chronological_split(frame: pd.DataFrame, split_config: SplitConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    split_config.validate()
    unique_times = frame["window_start"].sort_values().drop_duplicates().tolist()
    total_times = len(unique_times)
    if total_times < 3:
        raise ValueError("Need at least 3 distinct windows to build train/val/test splits")

    train_end_idx = max(1, int(total_times * split_config.train_ratio))
    val_end_idx = max(train_end_idx + 1, int(total_times * (split_config.train_ratio + split_config.val_ratio)))
    train_times = set(unique_times[:train_end_idx])
    val_times = set(unique_times[train_end_idx:val_end_idx])
    test_times = set(unique_times[val_end_idx:])

    train = frame[frame["window_start"].isin(train_times)].copy()
    val = frame[frame["window_start"].isin(val_times)].copy()
    test = frame[frame["window_start"].isin(test_times)].copy()

    assert_no_time_leakage(
        train_end=train["window_start"].max(),
        val_start=val["window_start"].min(),
        test_start=test["window_start"].min(),
    )
    return train, val, test


def write_report(report_path: Path, version: str, label_column: str, frame: pd.DataFrame, train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> None:
    summary = summarize_quality(frame, label_column)
    lines = [
        f"# Dataset Quality Report: {version}",
        "",
        f"- label: `{label_column}`",
        f"- total rows: {summary.row_count}",
        f"- duplicate keys: {summary.duplicate_rows}",
        f"- label min: {summary.min_label}",
        f"- label max: {summary.max_label}",
        f"- train rows: {len(train)}",
        f"- val rows: {len(val)}",
        f"- test rows: {len(test)}",
        f"- column count: {len(frame.columns)}",
        "",
        "## Missing Rate By Column",
    ]
    for column, ratio in summary.missing_rate_by_column.items():
        lines.append(f"- {column}: {ratio:.6f}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_full_report(report_path: Path, version: str, label_column: str, frame: pd.DataFrame) -> None:
    summary = summarize_quality(frame, label_column)
    lines = [
        f"# Dataset Quality Report: {version}",
        "",
        f"- label: `{label_column}`",
        f"- total rows: {summary.row_count}",
        f"- duplicate keys: {summary.duplicate_rows}",
        f"- label min: {summary.min_label}",
        f"- label max: {summary.max_label}",
        f"- split mode: full_only",
        f"- column count: {len(frame.columns)}",
        "",
        "## Missing Rate By Column",
    ]
    for column, ratio in summary.missing_rate_by_column.items():
        lines.append(f"- {column}: {ratio:.6f}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    report_path = Path(args.report_path)

    frame = load_frame(input_path)
    validate_columns(frame)
    built = build_features(frame, args.label)

    output_dir.mkdir(parents=True, exist_ok=True)
    if args.split_mode == "chronological":
        train, val, test = chronological_split(built, SplitConfig())
        train.to_parquet(output_dir / "train.parquet", index=False)
        val.to_parquet(output_dir / "val.parquet", index=False)
        test.to_parquet(output_dir / "test.parquet", index=False)

        metadata = {
            "version": args.version,
            "label": args.label,
            "split_mode": args.split_mode,
            "row_count": len(built),
            "train_rows": len(train),
            "val_rows": len(val),
            "test_rows": len(test),
            "columns": list(built.columns),
        }
        (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        write_report(report_path, args.version, args.label, built, train, val, test)
        return

    built.to_parquet(output_dir / "full.parquet", index=False)
    metadata = {
        "version": args.version,
        "label": args.label,
        "split_mode": args.split_mode,
        "row_count": len(built),
        "full_rows": len(built),
        "columns": list(built.columns),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    write_full_report(report_path, args.version, args.label, built)


if __name__ == "__main__":
    main()
