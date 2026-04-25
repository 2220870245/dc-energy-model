"""Combine baseline and deep-model metrics into one comparison benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline-json",
        required=True,
        help="Path to baseline benchmark.json output",
    )
    parser.add_argument(
        "--deep-dir",
        required=True,
        help="Directory containing *_metrics.json outputs from deep-model training",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for comparison benchmark outputs",
    )
    return parser.parse_args()


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def build_baseline_rows(path: Path) -> list[dict[str, object]]:
    payload = load_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected baseline benchmark list in {path}")

    rows: list[dict[str, object]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "family": "baseline",
                "model": item["model"],
                "context_length": None,
                "epochs": None,
                "batch_size": None,
                "learning_rate": None,
                "val_mae": item["val"]["mae"],
                "val_rmse": item["val"]["rmse"],
                "val_r2": item["val"]["r2"],
                "test_mae": item["test"]["mae"],
                "test_rmse": item["test"]["rmse"],
                "test_r2": item["test"]["r2"],
            }
        )
    return rows


def build_deep_rows(deep_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for metrics_path in sorted(deep_dir.glob("*_metrics.json")):
        item = load_json(metrics_path)
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "family": "deep",
                "model": item["model"],
                "context_length": item.get("context_length"),
                "epochs": item.get("epochs"),
                "batch_size": item.get("batch_size"),
                "learning_rate": item.get("learning_rate"),
                "val_mae": item["val_metrics"]["mae"],
                "val_rmse": item["val_metrics"]["rmse"],
                "val_r2": item["val_metrics"]["r2"],
                "test_mae": item["test_metrics"]["mae"],
                "test_rmse": item["test_metrics"]["rmse"],
                "test_r2": item["test_metrics"]["r2"],
            }
        )
    if not rows:
        raise ValueError(f"No deep-model metrics were found in {deep_dir}")
    return rows


def build_summary(comparison: pd.DataFrame) -> str:
    best_overall = comparison.iloc[0]
    deep_only = comparison.loc[comparison["family"] == "deep"].reset_index(drop=True)
    best_deep = deep_only.iloc[0]
    best_baseline = comparison.loc[comparison["family"] == "baseline"].reset_index(drop=True).iloc[0]

    mae_gap = float(best_deep["test_mae"]) - float(best_baseline["test_mae"])
    rmse_gap = float(best_deep["test_rmse"]) - float(best_baseline["test_rmse"])
    r2_gap = float(best_deep["test_r2"]) - float(best_baseline["test_r2"])

    lines = [
        "# Model Comparison Summary",
        "",
        f"- best overall model: `{best_overall['model']}` ({best_overall['family']})",
        f"- best deep model: `{best_deep['model']}`",
        f"- best baseline model: `{best_baseline['model']}`",
        f"- deep vs baseline test_mae gap: {mae_gap}",
        f"- deep vs baseline test_rmse gap: {rmse_gap}",
        f"- deep vs baseline test_r2 gap: {r2_gap}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    baseline_json = Path(args.baseline_json)
    deep_dir = Path(args.deep_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = build_baseline_rows(baseline_json) + build_deep_rows(deep_dir)
    comparison = (
        pd.DataFrame(rows)
        .sort_values(["test_mae", "test_rmse", "test_r2"], ascending=[True, True, False])
        .reset_index(drop=True)
    )
    comparison.to_csv(output_dir / "comparison.csv", index=False)
    (output_dir / "comparison.json").write_text(
        json.dumps(rows, indent=2),
        encoding="utf-8",
    )
    (output_dir / "comparison_summary.md").write_text(
        build_summary(comparison),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
