"""Train PyTorch sequence models on the processed dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from data.sequence_dataset import DEFAULT_SEQUENCE_FEATURES, PDUPowerSequenceDataset
from evaluation.metrics import evaluate_regression
from models.sequence_models import build_sequence_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", required=True, help="Processed dataset directory")
    parser.add_argument("--output-dir", required=True, help="Output directory for checkpoints and reports")
    parser.add_argument("--model", choices=["lstm", "transformer"], default="lstm")
    parser.add_argument("--label", default="measured_power_util")
    parser.add_argument("--context-length", type=int, default=12)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def load_split(dataset_dir: Path, split_name: str) -> pd.DataFrame:
    return pd.read_parquet(dataset_dir / f"{split_name}.parquet")


def make_loader(
    frame: pd.DataFrame,
    feature_columns: list[str],
    label_column: str,
    context_length: int,
    batch_size: int,
    shuffle: bool,
) -> tuple[PDUPowerSequenceDataset, DataLoader]:
    dataset = PDUPowerSequenceDataset(
        frame=frame,
        feature_columns=feature_columns,
        label_column=label_column,
        context_length=context_length,
    )
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)
    return dataset, loader


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
) -> float:
    training = optimizer is not None
    model.train(mode=training)
    total_loss = 0.0
    total_items = 0

    for features, targets in loader:
        features = features.to(device)
        targets = targets.to(device)
        predictions = model(features)
        loss = criterion(predictions, targets)

        if training:
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        batch_size = int(features.size(0))
        total_loss += float(loss.item()) * batch_size
        total_items += batch_size

    return total_loss / max(total_items, 1)


@torch.no_grad()
def collect_predictions(model: nn.Module, loader: DataLoader, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    preds: list[np.ndarray] = []
    truths: list[np.ndarray] = []
    for features, targets in loader:
        predictions = model(features.to(device)).cpu().numpy()
        preds.append(predictions.reshape(-1))
        truths.append(targets.numpy().reshape(-1))
    return np.concatenate(truths), np.concatenate(preds)


def main() -> None:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_frame = load_split(dataset_dir, "train")
    val_frame = load_split(dataset_dir, "val")
    test_frame = load_split(dataset_dir, "test")

    feature_columns = list(DEFAULT_SEQUENCE_FEATURES)
    train_dataset, train_loader = make_loader(
        frame=train_frame,
        feature_columns=feature_columns,
        label_column=args.label,
        context_length=args.context_length,
        batch_size=args.batch_size,
        shuffle=True,
    )
    _, val_loader = make_loader(
        frame=val_frame,
        feature_columns=feature_columns,
        label_column=args.label,
        context_length=args.context_length,
        batch_size=args.batch_size,
        shuffle=False,
    )
    _, test_loader = make_loader(
        frame=test_frame,
        feature_columns=feature_columns,
        label_column=args.label,
        context_length=args.context_length,
        batch_size=args.batch_size,
        shuffle=False,
    )

    device = torch.device(args.device)
    model = build_sequence_model(args.model, input_size=train_dataset.features.shape[-1]).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    criterion = nn.MSELoss()

    history: list[dict[str, float]] = []
    best_val_loss = float("inf")
    checkpoint_path = output_dir / f"{args.model}_best.pt"

    for epoch in range(1, args.epochs + 1):
        train_loss = run_epoch(model, train_loader, criterion, device, optimizer)
        val_loss = run_epoch(model, val_loader, criterion, device, optimizer=None)
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(
                {
                    "model": args.model,
                    "state_dict": model.state_dict(),
                    "feature_columns": feature_columns,
                    "context_length": args.context_length,
                    "label": args.label,
                },
                checkpoint_path,
            )

    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["state_dict"])

    val_true, val_pred = collect_predictions(model, val_loader, device)
    test_true, test_pred = collect_predictions(model, test_loader, device)
    results = {
        "model": args.model,
        "label": args.label,
        "context_length": args.context_length,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "feature_columns": feature_columns,
        "best_val_loss": best_val_loss,
        "history": history,
        "val_metrics": evaluate_regression(val_true, val_pred),
        "test_metrics": evaluate_regression(test_true, test_pred),
    }

    (output_dir / f"{args.model}_metrics.json").write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )
    summary = [
        f"# Deep Model Summary: {args.model}",
        "",
        f"- best_val_loss: {best_val_loss}",
        f"- test_mae: {results['test_metrics']['mae']}",
        f"- test_rmse: {results['test_metrics']['rmse']}",
        f"- test_r2: {results['test_metrics']['r2']}",
    ]
    (output_dir / f"{args.model}_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
