"""Run repeated-seed deep-model and baseline holdout evaluations and summarize stability."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-config", required=True, help="Path to the deep-model training config JSON")
    parser.add_argument("--holdout-path", required=True, help="Path to the holdout parquet or csv file")
    parser.add_argument("--output-dir", required=True, help="Directory for repeated-run outputs")
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python executable used to invoke the training and evaluation entrypoints",
    )
    parser.add_argument(
        "--seed",
        action="append",
        dest="seeds",
        type=int,
        help="Seed to run. Repeat this argument for multiple seeds. Defaults to 42, 7, 21.",
    )
    parser.add_argument(
        "--baseline-model",
        action="append",
        dest="baseline_models",
        default=None,
        help="Baseline model to compare on holdout. Repeat this argument for multiple models. Defaults to random_forest.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Reuse existing per-seed outputs if the expected metrics files already exist",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def config_to_cli_args(config: dict[str, Any], seed: int, output_dir: Path) -> list[str]:
    args: list[str] = []
    for key, value in config.items():
        if key in {"output_dir", "seed"} or value is None:
            continue
        flag = f"--{key.replace('_', '-')}"
        args.extend([flag, str(value)])
    args.extend(["--seed", str(seed), "--output-dir", str(output_dir)])
    return args


def run_command(command: list[str]) -> None:
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def mean_std(values: list[float]) -> dict[str, float]:
    return {
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
    }


def summarize_metric_block(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, float]]:
    metric_names = ("mae", "rmse", "r2")
    return {
        metric_name: mean_std([float(row[key][metric_name]) for row in rows])
        for metric_name in metric_names
    }


def winner_counts(
    deep_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    baseline_name: str,
) -> dict[str, int]:
    baseline_by_seed = {
        int(row["seed"]): row
        for row in baseline_rows
        if str(row["model"]) == baseline_name
    }
    counts = {"mae": 0, "rmse": 0, "r2": 0}
    for deep_row in deep_rows:
        seed = int(deep_row["seed"])
        baseline_row = baseline_by_seed.get(seed)
        if baseline_row is None:
            continue
        if float(deep_row["holdout_metrics"]["mae"]) < float(baseline_row["holdout"]["mae"]):
            counts["mae"] += 1
        if float(deep_row["holdout_metrics"]["rmse"]) < float(baseline_row["holdout"]["rmse"]):
            counts["rmse"] += 1
        if float(deep_row["holdout_metrics"]["r2"]) > float(baseline_row["holdout"]["r2"]):
            counts["r2"] += 1
    return counts


def main() -> None:
    args = parse_args()
    seeds = args.seeds or [42, 7, 21]
    baseline_models = args.baseline_models or ["random_forest"]
    train_config_path = Path(args.train_config)
    holdout_path = Path(args.holdout_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_json(train_config_path)
    if not isinstance(config, dict):
        raise ValueError("Training config must be a JSON object.")
    if "dataset_dir" not in config:
        raise ValueError("Training config must define dataset_dir.")
    if "model" not in config:
        raise ValueError("Training config must define model.")

    dataset_dir = Path(str(config["dataset_dir"]))
    model_name = str(config["model"])
    deep_rows: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []

    for seed in seeds:
        deep_train_dir = output_dir / "deep-models" / f"seed{seed}"
        holdout_deep_dir = output_dir / "holdout" / "lstm" / f"seed{seed}"
        holdout_baseline_dir = output_dir / "holdout" / "baselines" / f"seed{seed}"

        deep_metrics_path = deep_train_dir / f"{model_name}_metrics.json"
        holdout_metrics_path = holdout_deep_dir / "holdout_metrics.json"
        baseline_metrics_path = holdout_baseline_dir / "holdout_benchmark.json"

        if not (args.skip_existing and deep_metrics_path.exists()):
            run_command(
                [
                    args.python_executable,
                    "src/training/train_deep_models.py",
                    *config_to_cli_args(config, seed, deep_train_dir),
                ]
            )
        if not (args.skip_existing and holdout_metrics_path.exists()):
            run_command(
                [
                    args.python_executable,
                    "src/training/evaluate_sequence_holdout.py",
                    "--holdout-path",
                    str(holdout_path),
                    "--checkpoint",
                    str(deep_train_dir / f"{model_name}_best.pt"),
                    "--output-dir",
                    str(holdout_deep_dir),
                ]
            )
        if not (args.skip_existing and baseline_metrics_path.exists()):
            baseline_command = [
                args.python_executable,
                "src/training/evaluate_baselines_holdout.py",
                "--dataset-dir",
                str(dataset_dir),
                "--holdout-path",
                str(holdout_path),
                "--output-dir",
                str(holdout_baseline_dir),
                "--random-seed",
                str(seed),
            ]
            baseline_command.extend(["--models", *baseline_models])
            run_command(baseline_command)

        deep_metrics = load_json(deep_metrics_path)
        holdout_metrics = load_json(holdout_metrics_path)
        deep_rows.append(
            {
                "seed": seed,
                "checkpoint": str(deep_train_dir / f"{model_name}_best.pt"),
                "best_epoch": int(deep_metrics["best_epoch"]),
                "test_metrics": deep_metrics["test_metrics"],
                "holdout_metrics": holdout_metrics["holdout_metrics"],
            }
        )

        baseline_metrics = load_json(baseline_metrics_path)
        if not isinstance(baseline_metrics, list):
            raise ValueError("Baseline holdout benchmark JSON must be a list.")
        for row in baseline_metrics:
            row["seed"] = seed
            baseline_rows.append(row)

    summary_payload = {
        "train_config": str(train_config_path),
        "holdout_path": str(holdout_path),
        "python_executable": args.python_executable,
        "seeds": seeds,
        "baseline_models": baseline_models,
        "deep_model": model_name,
        "deep_runs": deep_rows,
        "baseline_runs": baseline_rows,
        "deep_test_summary": summarize_metric_block(deep_rows, "test_metrics"),
        "deep_holdout_summary": summarize_metric_block(deep_rows, "holdout_metrics"),
        "baseline_summaries": {},
        "winner_counts_vs_random_forest": winner_counts(deep_rows, baseline_rows, "random_forest"),
    }
    for baseline_model in baseline_models:
        model_rows = [row for row in baseline_rows if str(row["model"]) == baseline_model]
        if not model_rows:
            continue
        summary_payload["baseline_summaries"][baseline_model] = {
            "test": summarize_metric_block(model_rows, "test"),
            "holdout": summarize_metric_block(model_rows, "holdout"),
        }

    metrics_table_rows: list[dict[str, Any]] = []
    baseline_by_seed_model = {
        (int(row["seed"]), str(row["model"])): row
        for row in baseline_rows
    }
    for deep_row in deep_rows:
        seed = int(deep_row["seed"])
        table_row: dict[str, Any] = {
            "seed": seed,
            "lstm_test_mae": float(deep_row["test_metrics"]["mae"]),
            "lstm_test_rmse": float(deep_row["test_metrics"]["rmse"]),
            "lstm_test_r2": float(deep_row["test_metrics"]["r2"]),
            "lstm_holdout_mae": float(deep_row["holdout_metrics"]["mae"]),
            "lstm_holdout_rmse": float(deep_row["holdout_metrics"]["rmse"]),
            "lstm_holdout_r2": float(deep_row["holdout_metrics"]["r2"]),
            "best_epoch": int(deep_row["best_epoch"]),
        }
        for baseline_model in baseline_models:
            baseline_row = baseline_by_seed_model.get((seed, baseline_model))
            if baseline_row is None:
                continue
            prefix = baseline_model
            table_row[f"{prefix}_test_mae"] = float(baseline_row["test"]["mae"])
            table_row[f"{prefix}_test_rmse"] = float(baseline_row["test"]["rmse"])
            table_row[f"{prefix}_test_r2"] = float(baseline_row["test"]["r2"])
            table_row[f"{prefix}_holdout_mae"] = float(baseline_row["holdout"]["mae"])
            table_row[f"{prefix}_holdout_rmse"] = float(baseline_row["holdout"]["rmse"])
            table_row[f"{prefix}_holdout_r2"] = float(baseline_row["holdout"]["r2"])
        metrics_table_rows.append(table_row)

    metrics_table = pd.DataFrame(metrics_table_rows).sort_values("seed").reset_index(drop=True)
    metrics_table.to_csv(output_dir / "stability_metrics.csv", index=False)
    (output_dir / "stability_metrics.json").write_text(
        json.dumps(summary_payload, indent=2),
        encoding="utf-8",
    )

    holdout_summary = summary_payload["deep_holdout_summary"]
    test_summary = summary_payload["deep_test_summary"]
    summary_lines = [
        "# Holdout Stability Summary",
        "",
        f"- deep_model: `{model_name}`",
        f"- seeds: {', '.join(str(seed) for seed in seeds)}",
        f"- holdout: `{holdout_path.as_posix()}`",
        f"- python: `{args.python_executable}`",
        "",
        "## Deep Model Aggregate",
        "",
        f"- test mean: `{test_summary['mae']['mean']:.10f} / {test_summary['rmse']['mean']:.10f} / {test_summary['r2']['mean']:.10f}`",
        f"- test std: `{test_summary['mae']['std']:.10f} / {test_summary['rmse']['std']:.10f} / {test_summary['r2']['std']:.10f}`",
        f"- holdout mean: `{holdout_summary['mae']['mean']:.10f} / {holdout_summary['rmse']['mean']:.10f} / {holdout_summary['r2']['mean']:.10f}`",
        f"- holdout std: `{holdout_summary['mae']['std']:.10f} / {holdout_summary['rmse']['std']:.10f} / {holdout_summary['r2']['std']:.10f}`",
        "",
        "## Per-Seed Deep Model",
        "",
        "| seed | best_epoch | test_mae | test_rmse | test_r2 | holdout_mae | holdout_rmse | holdout_r2 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in deep_rows:
        summary_lines.append(
            "| "
            f"{row['seed']} | {row['best_epoch']} | "
            f"{float(row['test_metrics']['mae']):.10f} | {float(row['test_metrics']['rmse']):.10f} | {float(row['test_metrics']['r2']):.10f} | "
            f"{float(row['holdout_metrics']['mae']):.10f} | {float(row['holdout_metrics']['rmse']):.10f} | {float(row['holdout_metrics']['r2']):.10f} |"
        )

    for baseline_model in baseline_models:
        model_summary = summary_payload["baseline_summaries"].get(baseline_model)
        if model_summary is None:
            continue
        summary_lines.extend(
            [
                "",
                f"## Baseline Aggregate: `{baseline_model}`",
                "",
                f"- test mean: `{model_summary['test']['mae']['mean']:.10f} / {model_summary['test']['rmse']['mean']:.10f} / {model_summary['test']['r2']['mean']:.10f}`",
                f"- test std: `{model_summary['test']['mae']['std']:.10f} / {model_summary['test']['rmse']['std']:.10f} / {model_summary['test']['r2']['std']:.10f}`",
                f"- holdout mean: `{model_summary['holdout']['mae']['mean']:.10f} / {model_summary['holdout']['rmse']['mean']:.10f} / {model_summary['holdout']['r2']['mean']:.10f}`",
                f"- holdout std: `{model_summary['holdout']['mae']['std']:.10f} / {model_summary['holdout']['rmse']['std']:.10f} / {model_summary['holdout']['r2']['std']:.10f}`",
                "",
                f"## Per-Seed Baseline: `{baseline_model}`",
                "",
                "| seed | test_mae | test_rmse | test_r2 | holdout_mae | holdout_rmse | holdout_r2 |",
                "|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        model_rows = [row for row in baseline_rows if str(row["model"]) == baseline_model]
        model_rows.sort(key=lambda item: int(item["seed"]))
        for row in model_rows:
            summary_lines.append(
                "| "
                f"{row['seed']} | {float(row['test']['mae']):.10f} | {float(row['test']['rmse']):.10f} | {float(row['test']['r2']):.10f} | "
                f"{float(row['holdout']['mae']):.10f} | {float(row['holdout']['rmse']):.10f} | {float(row['holdout']['r2']):.10f} |"
            )

    winner_counts_rf = summary_payload["winner_counts_vs_random_forest"]
    if "random_forest" in baseline_models:
        summary_lines.extend(
            [
                "",
                "## Winner Counts vs `random_forest`",
                "",
                f"- better MAE in `{winner_counts_rf['mae']}` / `{len(deep_rows)}` seeds",
                f"- better RMSE in `{winner_counts_rf['rmse']}` / `{len(deep_rows)}` seeds",
                f"- better R2 in `{winner_counts_rf['r2']}` / `{len(deep_rows)}` seeds",
            ]
        )

    (output_dir / "stability_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
