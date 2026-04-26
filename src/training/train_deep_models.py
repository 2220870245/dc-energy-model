"""Train PyTorch sequence models on the processed dataset."""

from __future__ import annotations

import argparse
import json
import random
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

from data.sequence_dataset import (
    PDUPowerSequenceDataset,
    SequenceStandardizer,
    collect_sequence_targets,
    get_sequence_feature_columns,
)
from evaluation.metrics import evaluate_regression
from models.sequence_models import build_sequence_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", required=True, help="Processed dataset directory")
    parser.add_argument("--output-dir", required=True, help="Output directory for checkpoints and reports")
    parser.add_argument("--model", choices=["lstm", "transformer"], default="lstm")
    parser.add_argument(
        "--feature-set",
        choices=["legacy", "cyclic", "compact", "enhanced", "flex"],
        default="enhanced",
    )
    parser.add_argument("--label", default="measured_power_util")
    parser.add_argument("--target-mode", choices=["absolute", "residual"], default="absolute")
    parser.add_argument("--context-length", type=int, default=12)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--patience", type=int, default=12)
    parser.add_argument("--min-epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--loss", choices=["mse", "huber"], default="mse")
    parser.add_argument("--huber-delta", type=float, default=1.0)
    parser.add_argument("--target-scaling", choices=["standard", "none"], default="standard")
    parser.add_argument("--scheduler", choices=["none", "plateau"], default="none")
    parser.add_argument("--scheduler-patience", type=int, default=4)
    parser.add_argument("--scheduler-factor", type=float, default=0.5)
    parser.add_argument("--scheduler-min-lr", type=float, default=1e-5)
    parser.add_argument("--hidden-size", type=int, default=64)
    parser.add_argument("--num-layers", type=int, default=2)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--nhead", type=int, default=4)
    parser.add_argument("--pooling", choices=["last", "mean", "last_mean"], default="last")
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=42)
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


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def configure_target_scaling(
    standardizer: SequenceStandardizer,
    target_scaling: str,
) -> SequenceStandardizer:
    if target_scaling == "standard":
        return standardizer
    if target_scaling == "none":
        return SequenceStandardizer(
            feature_mean=standardizer.feature_mean,
            feature_std=standardizer.feature_std,
            target_mean=0.0,
            target_std=1.0,
        )
    raise ValueError(f"Unknown target scaling: {target_scaling}")


def build_loss(loss_name: str, huber_delta: float) -> nn.Module:
    if loss_name == "mse":
        return nn.MSELoss()
    if loss_name == "huber":
        return nn.HuberLoss(delta=huber_delta)
    raise ValueError(f"Unknown loss: {loss_name}")


def make_loader(
    frame: pd.DataFrame,
    feature_columns: list[str],
    label_column: str,
    context_length: int,
    batch_size: int,
    shuffle: bool,
    history_frame: pd.DataFrame | None,
    standardizer: SequenceStandardizer,
) -> tuple[PDUPowerSequenceDataset, DataLoader]:
    dataset = PDUPowerSequenceDataset(
        frame=frame,
        feature_columns=feature_columns,
        label_column=label_column,
        context_length=context_length,
        history_frame=history_frame,
        standardizer=standardizer,
    )
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)
    return dataset, loader


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
    grad_clip: float,
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
            if grad_clip > 0:
                nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()

        batch_size = int(features.size(0))
        total_loss += float(loss.item()) * batch_size
        total_items += batch_size

    return total_loss / max(total_items, 1)


@torch.no_grad()
def collect_predictions(
    model: nn.Module,
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
    set_seed(args.seed)
    dataset_dir = Path(args.dataset_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_train_frame = load_split(dataset_dir, "train")
    raw_val_frame = load_split(dataset_dir, "val")
    raw_test_frame = load_split(dataset_dir, "test")
    train_frame, target_column = prepare_target_frame(raw_train_frame, args.label, args.target_mode)
    val_frame, _ = prepare_target_frame(raw_val_frame, args.label, args.target_mode)
    test_frame, _ = prepare_target_frame(raw_test_frame, args.label, args.target_mode)

    feature_columns = get_sequence_feature_columns(args.feature_set)
    missing_features = [column for column in feature_columns if column not in train_frame.columns]
    if missing_features:
        raise ValueError(
            "Dataset is missing required feature columns for "
            f"feature_set={args.feature_set}: {missing_features}"
        )
    standardizer = SequenceStandardizer.fit(
        frame=train_frame,
        feature_columns=feature_columns,
        label_column=target_column,
        context_length=args.context_length,
    )
    standardizer = configure_target_scaling(standardizer, args.target_scaling)

    train_dataset, train_loader = make_loader(
        frame=train_frame,
        feature_columns=feature_columns,
        label_column=target_column,
        context_length=args.context_length,
        batch_size=args.batch_size,
        shuffle=True,
        history_frame=None,
        standardizer=standardizer,
    )
    val_history = train_frame
    val_dataset, val_loader = make_loader(
        frame=val_frame,
        feature_columns=feature_columns,
        label_column=target_column,
        context_length=args.context_length,
        batch_size=args.batch_size,
        shuffle=False,
        history_frame=val_history,
        standardizer=standardizer,
    )
    test_history = pd.concat([train_frame, val_frame], ignore_index=True)
    test_dataset, test_loader = make_loader(
        frame=test_frame,
        feature_columns=feature_columns,
        label_column=target_column,
        context_length=args.context_length,
        batch_size=args.batch_size,
        shuffle=False,
        history_frame=test_history,
        standardizer=standardizer,
    )

    device = torch.device(args.device)
    model = build_sequence_model(
        args.model,
        input_size=train_dataset.features.shape[-1],
        hidden_size=args.hidden_size,
        num_layers=args.num_layers,
        dropout=args.dropout,
        nhead=args.nhead,
        pooling=args.pooling,
    ).to(device)
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )
    scheduler: torch.optim.lr_scheduler.ReduceLROnPlateau | None = None
    if args.scheduler == "plateau":
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=args.scheduler_factor,
            patience=args.scheduler_patience,
            min_lr=args.scheduler_min_lr,
        )
    criterion = build_loss(args.loss, args.huber_delta)

    history: list[dict[str, float]] = []
    best_val_loss = float("inf")
    best_epoch = 0
    epochs_without_improvement = 0
    checkpoint_path = output_dir / f"{args.model}_best.pt"

    for epoch in range(1, args.epochs + 1):
        current_lr = float(optimizer.param_groups[0]["lr"])
        train_loss = run_epoch(
            model,
            train_loader,
            criterion,
            device,
            optimizer,
            grad_clip=args.grad_clip,
        )
        val_loss = run_epoch(
            model,
            val_loader,
            criterion,
            device,
            optimizer=None,
            grad_clip=args.grad_clip,
        )
        if scheduler is not None:
            scheduler.step(val_loss)
        next_lr = float(optimizer.param_groups[0]["lr"])
        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "learning_rate": current_lr,
                "next_learning_rate": next_lr,
            }
        )

        if val_loss < best_val_loss - 1e-8:
            best_val_loss = val_loss
            best_epoch = epoch
            epochs_without_improvement = 0
            torch.save(
                {
                    "model": args.model,
                    "feature_set": args.feature_set,
                    "state_dict": model.state_dict(),
                    "feature_columns": feature_columns,
                    "context_length": args.context_length,
                    "label": args.label,
                    "target_mode": args.target_mode,
                    "hidden_size": args.hidden_size,
                    "num_layers": args.num_layers,
                    "dropout": args.dropout,
                    "nhead": args.nhead,
                    "pooling": args.pooling,
                    "standardizer": {
                        "feature_mean": standardizer.feature_mean.tolist(),
                        "feature_std": standardizer.feature_std.tolist(),
                        "target_mean": standardizer.target_mean,
                        "target_std": standardizer.target_std,
                    },
                    "loss": args.loss,
                    "huber_delta": args.huber_delta,
                    "target_scaling": args.target_scaling,
                },
                checkpoint_path,
            )
        else:
            epochs_without_improvement += 1
            if epoch >= args.min_epochs and epochs_without_improvement >= args.patience:
                break

    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["state_dict"])

    val_anchor = None
    test_anchor = None
    if args.target_mode == "residual":
        val_anchor = collect_sequence_targets(
            frame=raw_val_frame,
            value_column="prev_measured_power_util",
            context_length=args.context_length,
            history_frame=raw_train_frame,
        )
        test_anchor = collect_sequence_targets(
            frame=raw_test_frame,
            value_column="prev_measured_power_util",
            context_length=args.context_length,
            history_frame=pd.concat([raw_train_frame, raw_val_frame], ignore_index=True),
        )

    val_true, val_pred = collect_predictions(
        model,
        val_loader,
        device,
        standardizer,
        anchor_values=val_anchor,
    )
    test_true, test_pred = collect_predictions(
        model,
        test_loader,
        device,
        standardizer,
        anchor_values=test_anchor,
    )
    results = {
        "model": args.model,
        "feature_set": args.feature_set,
        "label": args.label,
        "target_mode": args.target_mode,
        "context_length": args.context_length,
        "epochs_requested": args.epochs,
        "epochs_trained": len(history),
        "best_epoch": best_epoch,
        "patience": args.patience,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "loss": args.loss,
        "huber_delta": args.huber_delta,
        "target_scaling": args.target_scaling,
        "scheduler": args.scheduler,
        "scheduler_patience": args.scheduler_patience,
        "scheduler_factor": args.scheduler_factor,
        "scheduler_min_lr": args.scheduler_min_lr,
        "hidden_size": args.hidden_size,
        "num_layers": args.num_layers,
        "dropout": args.dropout,
        "nhead": args.nhead,
        "pooling": args.pooling,
        "seed": args.seed,
        "feature_columns": feature_columns,
        "best_val_loss": best_val_loss,
        "sample_counts": {
            "train": train_dataset.sample_count,
            "val": val_dataset.sample_count,
            "test": test_dataset.sample_count,
        },
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
        f"- target_mode: {args.target_mode}",
        f"- feature_set: {args.feature_set}",
        f"- pooling: {args.pooling}",
        f"- loss: {args.loss}",
        f"- target_scaling: {args.target_scaling}",
        f"- scheduler: {args.scheduler}",
        f"- best_epoch: {best_epoch}",
        f"- epochs_trained: {len(history)}",
        f"- best_val_loss: {best_val_loss}",
        f"- test_mae: {results['test_metrics']['mae']}",
        f"- test_rmse: {results['test_metrics']['rmse']}",
        f"- test_r2: {results['test_metrics']['r2']}",
    ]
    (output_dir / f"{args.model}_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
