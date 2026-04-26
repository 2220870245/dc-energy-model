"""Join aggregated flexibility features into an existing processed dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


KEY_COLUMNS: list[str] = ["window_start", "cell", "pdu"]
FLEX_EXCLUDE: set[str] = {"window_index", "cell", "pdu", "window_start"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", required=True, help="Existing processed dataset directory")
    parser.add_argument("--flex-path", required=True, help="Flex windows parquet or csv path")
    parser.add_argument("--output-dir", required=True, help="Output dataset directory")
    parser.add_argument("--report-path", required=True, help="Markdown report path")
    parser.add_argument("--version", required=True, help="Version label")
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


def resolve_added_columns(base_columns: list[str], flex_columns: list[str]) -> list[str]:
    added: list[str] = []
    for column in flex_columns:
        if column in KEY_COLUMNS:
            continue
        if column in base_columns:
            added.append(f"flex_window_{column}")
        else:
            added.append(column)
    return added


def merge_split(frame: pd.DataFrame, flex: pd.DataFrame) -> pd.DataFrame:
    renamed_flex = flex.copy()
    rename_map = {column: f"flex_window_{column}" for column in flex.columns if column not in KEY_COLUMNS and column in frame.columns}
    if rename_map:
        renamed_flex = renamed_flex.rename(columns=rename_map)
    merged = frame.merge(renamed_flex, on=KEY_COLUMNS, how="left", validate="one_to_one")
    added_columns = resolve_added_columns(list(frame.columns), list(flex.columns))
    missing_rows = merged[added_columns].isna().all(axis=1).sum()
    if missing_rows:
        raise ValueError(f"Missing flexibility features for {missing_rows} rows")
    return merged


def write_report(
    report_path: Path,
    version: str,
    split_mode: str,
    split_counts: dict[str, int],
    flex_columns: list[str],
) -> None:
    lines = [
        f"# Flex Join Report: {version}",
        "",
        f"- split_mode: {split_mode}",
        f"- flex_feature_count: {len(flex_columns)}",
    ]
    for split_name, count in split_counts.items():
        lines.append(f"- {split_name} rows: {count}")
    lines.extend(
        [
            "",
            "## Added Flex Columns",
        ]
    )
    for column in flex_columns:
        lines.append(f"- {column}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    flex_path = Path(args.flex_path)
    output_dir = Path(args.output_dir)
    report_path = Path(args.report_path)

    flex = load_frame(flex_path)
    flex["window_start"] = pd.to_datetime(flex["window_start"], utc=True)
    source_flex_columns = [column for column in flex.columns if column not in FLEX_EXCLUDE]

    output_dir.mkdir(parents=True, exist_ok=True)
    split_counts: dict[str, int] = {}

    full_path = dataset_dir / "full.parquet"
    if full_path.exists():
        full = pd.read_parquet(full_path)
        full["window_start"] = pd.to_datetime(full["window_start"], utc=True)
        merged_full = merge_split(full, flex)
        merged_full.to_parquet(output_dir / "full.parquet", index=False)
        split_mode = "full_only"
        split_counts["full"] = len(merged_full)
        columns = list(merged_full.columns)
        flex_columns = resolve_added_columns(list(full.columns), source_flex_columns)
    else:
        split_mode = "chronological"
        columns = []
        for split_name in ("train", "val", "test"):
            split = pd.read_parquet(dataset_dir / f"{split_name}.parquet")
            split["window_start"] = pd.to_datetime(split["window_start"], utc=True)
            merged = merge_split(split, flex)
            merged.to_parquet(output_dir / f"{split_name}.parquet", index=False)
            split_counts[split_name] = len(merged)
            columns = list(merged.columns)
            flex_columns = resolve_added_columns(list(split.columns), source_flex_columns)

    metadata = {
        "version": args.version,
        "source_dataset_dir": str(dataset_dir),
        "flex_path": str(flex_path),
        "split_mode": split_mode,
        "columns": columns,
        "flex_columns": flex_columns,
        "split_counts": split_counts,
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    write_report(report_path, args.version, split_mode, split_counts, flex_columns)


if __name__ == "__main__":
    main()
