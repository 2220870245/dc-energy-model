"""Fit baseline models on a development split and evaluate on a holdout table."""

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
    parser.add_argument("--dataset-dir", required=True, help="Processed development dataset directory")
    parser.add_argument("--holdout-path", required=True, help="Path to holdout parquet or csv file")
    parser.add_argument("--output-dir", required=True, help="Directory for holdout evaluation outputs")
    parser.add_argument("--label", default="measured_power_util", help="Label column")
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="Optional model subset to evaluate; defaults to all registered baselines",
    )
    parser.add_argument("--random-seed", type=int, default=42, help="Random seed for stochastic baselines")
    return parser.parse_args()


def load_frame(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


def load_split(dataset_dir: Path, split_name: str) -> pd.DataFrame:
    return pd.read_parquet(dataset_dir / f"{split_name}.parquet")


def fit_and_score(
    model_name: str,
    feature_columns: list[str],
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    holdout: pd.DataFrame,
    label: str,
    random_seed: int,
) -> dict[str, object]:
    model = build_model(model_name, random_seed=random_seed)
    x_train = train[feature_columns].to_numpy()
    y_train = train[label].to_numpy()
    x_val = val[feature_columns].to_numpy()
    y_val = val[label].to_numpy()
    x_test = test[feature_columns].to_numpy()
    y_test = test[label].to_numpy()
    x_holdout = holdout[feature_columns].to_numpy()
    y_holdout = holdout[label].to_numpy()

    model.fit(x_train, y_train)
    val_pred = model.predict(x_val)
    test_pred = model.predict(x_test)
    holdout_pred = model.predict(x_holdout)

    return {
        "model": model_name,
        "random_seed": random_seed,
        "features": feature_columns,
        "val": evaluate_regression(y_val, val_pred),
        "test": evaluate_regression(y_test, test_pred),
        "holdout": evaluate_regression(y_holdout, holdout_pred),
    }


def main() -> None:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    holdout_path = Path(args.holdout_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train = load_split(dataset_dir, "train")
    val = load_split(dataset_dir, "val")
    test = load_split(dataset_dir, "test")
    holdout = load_frame(holdout_path)

    results = []
    feature_sets = default_feature_sets()
    if args.models:
        feature_sets = {name: feature_sets[name] for name in args.models}

    for model_name, feature_columns in feature_sets.items():
        missing = [column for column in feature_columns if column not in holdout.columns]
        if missing:
            raise ValueError(f"Holdout is missing columns for {model_name}: {missing}")
        results.append(
            fit_and_score(
                model_name,
                feature_columns,
                train,
                val,
                test,
                holdout,
                args.label,
                args.random_seed,
            )
        )

    rows = []
    for item in results:
        rows.append(
            {
                "model": item["model"],
                "val_mae": item["val"]["mae"],
                "test_mae": item["test"]["mae"],
                "holdout_mae": item["holdout"]["mae"],
                "holdout_rmse": item["holdout"]["rmse"],
                "holdout_r2": item["holdout"]["r2"],
            }
        )
    benchmark = pd.DataFrame(rows).sort_values(["holdout_mae", "holdout_rmse"]).reset_index(drop=True)
    benchmark.to_csv(output_dir / "holdout_benchmark.csv", index=False)
    (output_dir / "holdout_benchmark.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    best_row = benchmark.iloc[0].to_dict()
    summary_lines = [
        "# Baseline Holdout Summary",
        "",
        f"- best holdout model: `{best_row['model']}`",
        f"- holdout_mae: {best_row['holdout_mae']}",
        f"- holdout_rmse: {best_row['holdout_rmse']}",
        f"- holdout_r2: {best_row['holdout_r2']}",
    ]
    (output_dir / "holdout_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
