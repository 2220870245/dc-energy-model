"""Evaluate a saved sequence-model checkpoint on a holdout table."""

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

from data.sequence_dataset import PDUPowerSequenceDataset, SequenceStandardizer, collect_sequence_targets
from evaluation.metrics import evaluate_regression
from models.sequence_models import build_sequence_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--holdout-path", required=True, help="Path to holdout parquet or csv file")
    parser.add_argument("--checkpoint", required=True, help="Sequence model checkpoint path")
    parser.add_argument("--output-dir", required=True, help="Directory for holdout evaluation outputs")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def load_frame(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


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


@torch.no_grad()
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


def main() -> None:
    args = parse_args()
    holdout_path = Path(args.holdout_path)
    checkpoint_path = Path(args.checkpoint)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    holdout = load_frame(holdout_path)
    device = torch.device(args.device)
    checkpoint = torch.load(checkpoint_path, map_location=device)

    model_name = str(checkpoint["model"])
    label = str(checkpoint["label"])
    target_mode = str(checkpoint.get("target_mode", "absolute"))
    context_length = int(checkpoint["context_length"])
    feature_columns = list(checkpoint["feature_columns"])
    standardizer = restore_standardizer(checkpoint)

    prepared_holdout, target_column = prepare_target_frame(holdout, label, target_mode)
    dataset = PDUPowerSequenceDataset(
        frame=prepared_holdout,
        feature_columns=feature_columns,
        label_column=target_column,
        context_length=context_length,
        history_frame=None,
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
            frame=holdout,
            value_column="prev_measured_power_util",
            context_length=context_length,
            history_frame=None,
        )

    holdout_true, holdout_pred = collect_predictions(
        model=model,
        loader=loader,
        device=device,
        standardizer=standardizer,
        anchor_values=anchor_values,
    )

    results = {
        "checkpoint": str(checkpoint_path),
        "model": model_name,
        "label": label,
        "target_mode": target_mode,
        "context_length": context_length,
        "sample_count": dataset.sample_count,
        "holdout_metrics": evaluate_regression(holdout_true, holdout_pred),
    }
    (output_dir / "holdout_metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    summary_lines = [
        f"# Sequence Holdout Summary: {model_name}",
        "",
        f"- target_mode: {target_mode}",
        f"- context_length: {context_length}",
        f"- sample_count: {dataset.sample_count}",
        f"- holdout_mae: {results['holdout_metrics']['mae']}",
        f"- holdout_rmse: {results['holdout_metrics']['rmse']}",
        f"- holdout_r2: {results['holdout_metrics']['r2']}",
    ]
    (output_dir / "holdout_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
