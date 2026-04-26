"""Build 5-minute flexibility windows from task-level Google cluster traces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

WINDOW_US = 300_000_000
JOB_COLLECTION_TYPE = 0
SCHEDULER_BATCH = 1


REQUIRED_COLUMNS: tuple[str, ...] = (
    "window_start",
    "window_index",
    "cell",
    "pdu",
    "start_time",
    "end_time",
    "collection_id",
    "instance_index",
    "machine_id",
    "alloc_collection_id",
    "collection_type",
    "collection_submit_time",
    "collection_schedule_time",
    "collection_end_time",
    "collection_scheduling_class",
    "collection_priority",
    "preferred_scheduler",
    "dependency_count",
    "instance_submit_time",
    "instance_queue_time",
    "instance_enable_time",
    "instance_start_time",
    "instance_end_time",
    "instance_scheduling_class",
    "instance_priority",
    "avg_cpu_usage",
    "max_cpu_usage",
    "measured_power_util",
    "production_power_util",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to the exported task trace csv or parquet")
    parser.add_argument("--output-dir", required=True, help="Directory for aggregated outputs")
    parser.add_argument("--report-path", required=True, help="Markdown report path")
    parser.add_argument("--rho", type=float, default=1.5, help="Deadline slack multiplier")
    parser.add_argument(
        "--max-flex-scheduling-class",
        type=int,
        default=1,
        help="Largest scheduling_class treated as flex-eligible",
    )
    parser.add_argument(
        "--require-batch-scheduler",
        action="store_true",
        help="Require preferred_scheduler == SCHEDULER_BATCH for flex-eligible jobs",
    )
    parser.add_argument(
        "--version",
        default="google_flex_v1",
        help="Version label written into metadata",
    )
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


def first_present(frame: pd.DataFrame, columns: list[str], default: float | int = 0) -> pd.Series:
    numeric = frame.loc[:, columns].apply(pd.to_numeric, errors="coerce")
    return numeric.bfill(axis=1).iloc[:, 0].fillna(default)


def build_task_states(
    frame: pd.DataFrame,
    rho: float,
    max_flex_scheduling_class: int,
    require_batch_scheduler: bool,
) -> pd.DataFrame:
    built = frame.copy()
    built["window_start"] = pd.to_datetime(built["window_start"], utc=True)

    numeric_columns = [
        "start_time",
        "end_time",
        "collection_submit_time",
        "collection_schedule_time",
        "collection_end_time",
        "collection_scheduling_class",
        "collection_priority",
        "preferred_scheduler",
        "dependency_count",
        "instance_submit_time",
        "instance_queue_time",
        "instance_enable_time",
        "instance_start_time",
        "instance_end_time",
        "instance_scheduling_class",
        "instance_priority",
        "avg_cpu_usage",
        "max_cpu_usage",
        "measured_power_util",
        "production_power_util",
        "alloc_collection_id",
        "collection_type",
    ]
    for column in numeric_columns:
        built[column] = pd.to_numeric(built[column], errors="coerce")

    built["submit_time_us"] = first_present(
        built,
        ["instance_submit_time", "collection_submit_time", "start_time"],
        default=0,
    )
    built["run_start_time_us"] = first_present(
        built,
        ["instance_start_time", "collection_schedule_time", "start_time"],
        default=0,
    )
    built["run_end_time_us"] = first_present(
        built,
        ["instance_end_time", "collection_end_time", "end_time"],
        default=0,
    )

    built["actual_runtime_us"] = (built["run_end_time_us"] - built["run_start_time_us"]).clip(lower=WINDOW_US)
    built["proxy_deadline_us"] = built["submit_time_us"] + rho * built["actual_runtime_us"]
    built["remaining_slack_us"] = built["proxy_deadline_us"] - (built["end_time"] + built["actual_runtime_us"])

    built["effective_scheduling_class"] = (
        built["instance_scheduling_class"]
        .fillna(built["collection_scheduling_class"])
        .fillna(99)
        .astype(int)
    )
    built["effective_priority"] = (
        built["instance_priority"]
        .fillna(built["collection_priority"])
        .fillna(0)
        .astype(int)
    )
    built["effective_scheduler"] = built["preferred_scheduler"].fillna(0).astype(int)
    built["is_job"] = built["collection_type"].fillna(JOB_COLLECTION_TYPE).astype(int) == JOB_COLLECTION_TYPE
    built["is_batch_scheduler"] = built["effective_scheduler"] == SCHEDULER_BATCH
    built["in_alloc_set"] = built["alloc_collection_id"].fillna(0).astype(int) != 0
    built["is_flex_candidate"] = built["is_job"] & (built["effective_scheduling_class"] <= max_flex_scheduling_class)
    if require_batch_scheduler:
        built["is_flex_candidate"] = built["is_flex_candidate"] & built["is_batch_scheduler"]
    built["is_critical"] = built["is_flex_candidate"] & (built["remaining_slack_us"] <= 0)
    built["is_deferrable"] = built["is_flex_candidate"] & ~built["is_critical"]
    built["is_online_like"] = ~built["is_flex_candidate"]

    return built


def aggregate_windows(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.groupby(["window_start", "window_index", "cell", "pdu"], sort=True)
    aggregated = grouped.apply(
        lambda group: pd.Series(
            {
                "task_count": int(len(group)),
                "job_count": int(group["collection_id"].nunique()),
                "machine_count": int(group["machine_id"].nunique()),
                "total_cpu_usage": float(group["avg_cpu_usage"].sum()),
                "online_cpu_usage": float(group.loc[group["is_online_like"], "avg_cpu_usage"].sum()),
                "flex_cpu_usage": float(group.loc[group["is_deferrable"], "avg_cpu_usage"].sum()),
                "critical_cpu_usage": float(group.loc[group["is_critical"], "avg_cpu_usage"].sum()),
                "batch_candidate_cpu_usage": float(group.loc[group["is_flex_candidate"], "avg_cpu_usage"].sum()),
                "online_task_count": int(group["is_online_like"].sum()),
                "deferrable_task_count": int(group["is_deferrable"].sum()),
                "critical_task_count": int(group["is_critical"].sum()),
                "mean_deferrable_slack_us": float(
                    group.loc[group["is_deferrable"], "remaining_slack_us"].mean()
                )
                if bool(group["is_deferrable"].any())
                else 0.0,
                "max_dependency_count": int(group["dependency_count"].fillna(0).max()),
                "mean_priority": float(group["effective_priority"].mean()),
                "measured_power_util": float(group["measured_power_util"].dropna().mean())
                if group["measured_power_util"].notna().any()
                else np.nan,
                "production_power_util": float(group["production_power_util"].dropna().mean())
                if group["production_power_util"].notna().any()
                else np.nan,
            }
        )
    )
    aggregated = aggregated.reset_index()
    aggregated["flex_cpu_ratio"] = np.where(
        aggregated["total_cpu_usage"] > 0,
        aggregated["flex_cpu_usage"] / aggregated["total_cpu_usage"],
        0.0,
    )
    aggregated["critical_cpu_ratio"] = np.where(
        aggregated["total_cpu_usage"] > 0,
        aggregated["critical_cpu_usage"] / aggregated["total_cpu_usage"],
        0.0,
    )
    aggregated["online_cpu_ratio"] = np.where(
        aggregated["total_cpu_usage"] > 0,
        aggregated["online_cpu_usage"] / aggregated["total_cpu_usage"],
        0.0,
    )
    return aggregated


def write_report(report_path: Path, version: str, rho: float, frame: pd.DataFrame, aggregated: pd.DataFrame) -> None:
    lines = [
        f"# Flexibility Window Report: {version}",
        "",
        f"- rho: `{rho}`",
        f"- task rows: {len(frame)}",
        f"- window rows: {len(aggregated)}",
        f"- unique PDUs: {frame[['cell', 'pdu']].drop_duplicates().shape[0]}",
        f"- flex candidate ratio: {frame['is_flex_candidate'].mean():.6f}",
        f"- deferrable ratio: {frame['is_deferrable'].mean():.6f}",
        f"- critical ratio: {frame['is_critical'].mean():.6f}",
        f"- mean window flex CPU ratio: {aggregated['flex_cpu_ratio'].mean():.6f}",
        f"- mean window critical CPU ratio: {aggregated['critical_cpu_ratio'].mean():.6f}",
        "",
        "## Scheduling Class Mix",
    ]
    for scheduling_class, count in frame["effective_scheduling_class"].value_counts(dropna=False).sort_index().items():
        lines.append(f"- class {scheduling_class}: {int(count)}")
    lines.extend(
        [
            "",
            "## Candidate Mix",
            f"- online_like_rows: {int(frame['is_online_like'].sum())}",
            f"- flex_candidate_rows: {int(frame['is_flex_candidate'].sum())}",
            f"- deferrable_rows: {int(frame['is_deferrable'].sum())}",
            f"- critical_rows: {int(frame['is_critical'].sum())}",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    report_path = Path(args.report_path)

    frame = load_frame(input_path)
    validate_columns(frame)
    built = build_task_states(
        frame=frame,
        rho=args.rho,
        max_flex_scheduling_class=args.max_flex_scheduling_class,
        require_batch_scheduler=args.require_batch_scheduler,
    )
    aggregated = aggregate_windows(built)

    output_dir.mkdir(parents=True, exist_ok=True)
    built.to_parquet(output_dir / "task_trace.parquet", index=False)
    aggregated.to_parquet(output_dir / "flex_windows.parquet", index=False)
    metadata = {
        "version": args.version,
        "rho": args.rho,
        "max_flex_scheduling_class": args.max_flex_scheduling_class,
        "require_batch_scheduler": args.require_batch_scheduler,
        "task_rows": len(built),
        "window_rows": len(aggregated),
        "columns": list(aggregated.columns),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    write_report(report_path, args.version, args.rho, built, aggregated)


if __name__ == "__main__":
    main()
