"""Package aggregated flexibility windows into a versioned dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS: tuple[str, ...] = (
    "window_start",
    "window_index",
    "cell",
    "pdu",
    "task_count",
    "job_count",
    "machine_count",
    "total_cpu_usage",
    "online_cpu_usage",
    "flex_cpu_usage",
    "critical_cpu_usage",
    "batch_candidate_cpu_usage",
    "online_task_count",
    "deferrable_task_count",
    "critical_task_count",
    "mean_deferrable_slack_us",
    "max_dependency_count",
    "mean_priority",
    "mean_scheduling_class",
    "flex_cpu_ratio",
    "critical_cpu_ratio",
    "online_cpu_ratio",
    "measured_power_util",
    "production_power_util",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to the aggregated flexibility csv or parquet")
    parser.add_argument("--output-dir", required=True, help="Directory for packaged outputs")
    parser.add_argument("--report-path", required=True, help="Markdown report path")
    parser.add_argument("--version", default="google_flex_windows_v1", help="Version label")
    return parser.parse_args()


def load_frame(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        header = "window_start,window_index,cell,pdu"
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()
        for idx, line in enumerate(lines):
            if line.startswith(header):
                return pd.read_csv(path, skiprows=idx)
        return pd.read_csv(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


def validate_columns(frame: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def build_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    built = frame.copy()
    built["window_start"] = pd.to_datetime(built["window_start"], utc=True)
    built = built.sort_values(["window_start", "cell", "pdu"]).reset_index(drop=True)
    return built


def safe_corr(frame: pd.DataFrame, left: str, right: str) -> float:
    subset = frame[[left, right]].dropna()
    if len(subset) < 2:
        return float("nan")
    return float(subset[left].corr(subset[right]))


def write_report(report_path: Path, version: str, frame: pd.DataFrame) -> None:
    lines = [
        f"# Flexibility Dataset Report: {version}",
        "",
        f"- rows: {len(frame)}",
        f"- unique PDUs: {frame[['cell', 'pdu']].drop_duplicates().shape[0]}",
        f"- min window_index: {int(frame['window_index'].min())}",
        f"- max window_index: {int(frame['window_index'].max())}",
        f"- mean task_count: {frame['task_count'].mean():.6f}",
        f"- mean total_cpu_usage: {frame['total_cpu_usage'].mean():.6f}",
        f"- mean flex_cpu_ratio: {frame['flex_cpu_ratio'].mean():.6f}",
        f"- mean critical_cpu_ratio: {frame['critical_cpu_ratio'].mean():.6f}",
        f"- mean online_cpu_ratio: {frame['online_cpu_ratio'].mean():.6f}",
        f"- corr(total_cpu_usage, measured_power_util): {safe_corr(frame, 'total_cpu_usage', 'measured_power_util'):.6f}",
        f"- corr(flex_cpu_ratio, measured_power_util): {safe_corr(frame, 'flex_cpu_ratio', 'measured_power_util'):.6f}",
        f"- corr(critical_cpu_ratio, measured_power_util): {safe_corr(frame, 'critical_cpu_ratio', 'measured_power_util'):.6f}",
        "",
        "## Per-PDU Mean Ratios",
    ]
    grouped = (
        frame.groupby(["cell", "pdu"], sort=True)[["flex_cpu_ratio", "critical_cpu_ratio", "online_cpu_ratio"]]
        .mean()
        .reset_index()
    )
    for row in grouped.itertuples(index=False):
        lines.append(
            f"- {row.cell}/{row.pdu}: "
            f"flex={row.flex_cpu_ratio:.6f}, "
            f"critical={row.critical_cpu_ratio:.6f}, "
            f"online={row.online_cpu_ratio:.6f}"
        )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    report_path = Path(args.report_path)

    frame = load_frame(input_path)
    validate_columns(frame)
    built = build_dataset(frame)

    output_dir.mkdir(parents=True, exist_ok=True)
    built.to_parquet(output_dir / "flex_windows.parquet", index=False)
    metadata = {
        "version": args.version,
        "row_count": len(built),
        "pdu_count": int(built[["cell", "pdu"]].drop_duplicates().shape[0]),
        "window_index_min": int(built["window_index"].min()),
        "window_index_max": int(built["window_index"].max()),
        "columns": list(built.columns),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    write_report(report_path, args.version, built)


if __name__ == "__main__":
    main()
