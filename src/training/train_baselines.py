"""Train baseline models on the processed dataset and publish a benchmark table."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evaluation.metrics import evaluate_regression
from models.baselines import build_model, default_feature_sets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", required=True, help="Processed dataset directory")
    parser.add_argument("--output-dir", required=True, help="Benchmark output directory")
    parser.add_argument("--label", default="measured_power_util", help="Label column")
    return parser.parse_args()


def load_split(dataset_dir: Path, split_name: str) -> pd.DataFrame:
    return pd.read_parquet(dataset_dir / f"{split_name}.parquet")


def fit_and_score(model_name: str, feature_columns: list[str], train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, label: str) -> dict[str, object]:
    model = build_model(model_name)
    x_train = train[feature_columns].to_numpy()
    y_train = train[label].to_numpy()
    x_val = val[feature_columns].to_numpy()
    y_val = val[label].to_numpy()
    x_test = test[feature_columns].to_numpy()
    y_test = test[label].to_numpy()

    model.fit(x_train, y_train)
    val_pred = model.predict(x_val)
    test_pred = model.predict(x_test)

    return {
        "model": model_name,
        "features": feature_columns,
        "val": evaluate_regression(y_val, val_pred),
        "test": evaluate_regression(y_test, test_pred),
    }


def main() -> None:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train = load_split(dataset_dir, "train")
    val = load_split(dataset_dir, "val")
    test = load_split(dataset_dir, "test")

    results = []
    feature_sets = default_feature_sets()
    for model_name, feature_columns in feature_sets.items():
        missing = [column for column in feature_columns if column not in train.columns]
        if missing:
            raise ValueError(f"Model {model_name} is missing columns: {missing}")
        results.append(fit_and_score(model_name, feature_columns, train, val, test, args.label))

    benchmark_rows = []
    for item in results:
        benchmark_rows.append(
            {
                "model": item["model"],
                "val_mae": item["val"]["mae"],
                "val_rmse": item["val"]["rmse"],
                "test_mae": item["test"]["mae"],
                "test_rmse": item["test"]["rmse"],
                "test_r2": item["test"]["r2"],
            }
        )

    benchmark = pd.DataFrame(benchmark_rows).sort_values(["test_mae", "test_rmse"]).reset_index(drop=True)
    benchmark.to_csv(output_dir / "benchmark.csv", index=False)
    (output_dir / "benchmark.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    best_row = benchmark.iloc[0].to_dict()
    summary_lines = [
        "# Baseline Benchmark Summary",
        "",
        f"- best model: `{best_row['model']}`",
        f"- test_mae: {best_row['test_mae']}",
        f"- test_rmse: {best_row['test_rmse']}",
        f"- test_r2: {best_row['test_r2']}",
    ]
    (output_dir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
