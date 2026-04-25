"""Evaluate a sequence-model ensemble from saved checkpoints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from data.sequence_dataset import (
    DEFAULT_SEQUENCE_FEATURES,
    PDUPowerSequenceDataset,
    SequenceStandardizer,
    collect_sequence_targets,
)
from evaluation.metrics import evaluate_regression
from models.sequence_models import build_sequence_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", required=True, help="Processed dataset directory")
    parser.add_argument("--output-dir", required=True, help="Directory for ensemble reports")
    parser.add_argument("--checkpoint", action="append", required=True, help="Sequence-model checkpoint path")
    parser.add_argument("--split", choices=["val", "test"], default="test")
    parser.add_argument("--name", default="sequence_ensemble", help="Label for the ensemble report")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def load_split(dataset_dir: Path, split_name: str) -> pd.DataFrame:
    return pd.read_parquet(dataset_dir / f"{split_name}.parquet")


def prepare_target_frame(frame: pd.DataFrame, label_column: str, target_mode: str) -> tuple[pd.DataFrame, str]:
    prepared = frame.copy()
    target_column = label_column
    if target_mode == "residual":
        target_column = f"{label_column}_residual"
        prepared[target_column] = prepared[label_column] - prepared["prev_measured_power_util"]
    return prepared, target_column


def restore_standardizer(payload: dict[str, object]) -> SequenceStandardizer:
    standardizer_payload = payload["standardizer"]
    if not isinstance(standardizer_payload, dict):
        raise ValueError("Checkpoint standardizer payload must be a dictionary.")
    return SequenceStandardizer(
        feature_mean=np.asarray(standardizer_payload["feature_mean"], dtype=np.float32),
        feature_std=np.asarray(standardizer_payload["feature_std"], dtype=np.float32),
        target_mean=float(standardizer_payload["target_mean"]),
        target_std=float(standardizer_payload["target_std"]),
    )


def collect_predictions(
    model: torch.nn.Module,
    loader: DataLoader,
    device: torch.device,
    standardizer: SequenceStandardizer,
    anchor_values: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    preds: list[np.ndarray] = []
    truths: list[np.ndarray] = []
    with torch.no_grad():
        for features, targets in loader:
            predictions = model(features.to(device)).cpu().numpy()
            preds.append(predictions.reshape(-1))
            truths.append(targets.numpy().reshape(-1))
    y_true = np.concatenate(truths)
    y_pred = np.concatenate(preds)
    restored_true = standardizer.inverse_targets(y_true)
    restored_pred = standardizer.inverse_targets(y_pred)
    if anchor_values is not None:
        restored_true = restored_true + anchor_values
        restored_pred = restored_pred + anchor_values
    return restored_true, restored_pred


def member_summary(checkpoint_path: Path, payload: dict[str, object], metrics: dict[str, float]) -> dict[str, object]:
    return {
        "checkpoint": str(checkpoint_path),
        "model": payload["model"],
        "label": payload["label"],
        "target_mode": payload.get("target_mode", "absolute"),
        "context_length": int(payload["context_length"]),
        "hidden_size": int(payload.get("hidden_size", 64)),
        "num_layers": int(payload.get("num_layers", 2)),
        "dropout": float(payload.get("dropout", 0.1)),
        "nhead": int(payload.get("nhead", 4)),
        "metrics": metrics,
    }


def mean_metrics(metric_list: list[dict[str, float]]) -> dict[str, float]:
    metric_names = metric_list[0].keys()
    return {
        name: float(np.mean([metrics[name] for metrics in metric_list]))
        for name in metric_names
    }


def main() -> None:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_train_frame = load_split(dataset_dir, "train")
    raw_val_frame = load_split(dataset_dir, "val")
    raw_test_frame = load_split(dataset_dir, "test")
    raw_frame = raw_val_frame if args.split == "val" else raw_test_frame
    raw_history_frame = raw_train_frame if args.split == "val" else pd.concat(
        [raw_train_frame, raw_val_frame],
        ignore_index=True,
    )
    device = torch.device(args.device)

    members: list[dict[str, object]] = []
    member_predictions: list[np.ndarray] = []
    shared_truth: np.ndarray | None = None

    for checkpoint_arg in args.checkpoint:
        checkpoint_path = Path(checkpoint_arg)
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model_name = str(checkpoint["model"])
        label = str(checkpoint["label"])
        target_mode = str(checkpoint.get("target_mode", "absolute"))
        context_length = int(checkpoint["context_length"])
        feature_columns = list(checkpoint.get("feature_columns", list(DEFAULT_SEQUENCE_FEATURES)))

        prepared_frame, target_column = prepare_target_frame(raw_frame, label, target_mode)
        prepared_history_frame, _ = prepare_target_frame(raw_history_frame, label, target_mode)
        standardizer = restore_standardizer(checkpoint)
        dataset = PDUPowerSequenceDataset(
            frame=prepared_frame,
            feature_columns=feature_columns,
            label_column=target_column,
            context_length=context_length,
            history_frame=prepared_history_frame,
            standardizer=standardizer,
        )
        loader = DataLoader(dataset, batch_size=256, shuffle=False)

        model = build_sequence_model(
            model_name,
            input_size=dataset.features.shape[-1],
            hidden_size=int(checkpoint.get("hidden_size", 64)),
            num_layers=int(checkpoint.get("num_layers", 2)),
            dropout=float(checkpoint.get("dropout", 0.1)),
            nhead=int(checkpoint.get("nhead", 4)),
        ).to(device)
        model.load_state_dict(checkpoint["state_dict"])

        anchor_values = None
        if target_mode == "residual":
            anchor_values = collect_sequence_targets(
                frame=raw_frame,
                value_column="prev_measured_power_util",
                context_length=context_length,
                history_frame=raw_history_frame,
            )

        y_true, y_pred = collect_predictions(
            model=model,
            loader=loader,
            device=device,
            standardizer=standardizer,
            anchor_values=anchor_values,
        )
        if shared_truth is None:
            shared_truth = y_true
        elif not np.allclose(shared_truth, y_true, atol=1e-6):
            raise ValueError("Ensemble members do not share the same target values.")

        metrics = evaluate_regression(y_true, y_pred)
        members.append(member_summary(checkpoint_path, checkpoint, metrics))
        member_predictions.append(y_pred)

    if shared_truth is None:
        raise ValueError("No ensemble members were evaluated.")

    ensemble_pred = np.mean(np.stack(member_predictions, axis=0), axis=0)
    ensemble_metrics = evaluate_regression(shared_truth, ensemble_pred)
    member_metric_mean = mean_metrics([member["metrics"] for member in members])  # type: ignore[index]

    results = {
        "name": args.name,
        "split": args.split,
        "member_count": len(members),
        "members": members,
        "member_metric_mean": member_metric_mean,
        "ensemble_metrics": ensemble_metrics,
    }
    (output_dir / "ensemble_metrics.json").write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    summary_lines = [
        f"# Sequence Ensemble Summary: {args.name}",
        "",
        f"- split: {args.split}",
        f"- member_count: {len(members)}",
        f"- member_mean_mae: {member_metric_mean['mae']}",
        f"- member_mean_rmse: {member_metric_mean['rmse']}",
        f"- member_mean_r2: {member_metric_mean['r2']}",
        f"- ensemble_mae: {ensemble_metrics['mae']}",
        f"- ensemble_rmse: {ensemble_metrics['rmse']}",
        f"- ensemble_r2: {ensemble_metrics['r2']}",
        "",
        "## Members",
        "",
    ]
    for member in members:
        metrics = member["metrics"]  # type: ignore[index]
        summary_lines.append(
            "- "
            f"{Path(str(member['checkpoint'])).parent.name}: "
            f"mae={metrics['mae']}, rmse={metrics['rmse']}, r2={metrics['r2']}"
        )
    (output_dir / "ensemble_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
