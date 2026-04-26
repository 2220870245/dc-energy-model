"""PyTorch sequence models for the energy model project."""

from __future__ import annotations

import math

import torch
from torch import nn


class LSTMRegressor(nn.Module):
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.1,
        pooling: str = "last",
    ) -> None:
        super().__init__()
        if pooling not in {"last", "mean", "last_mean"}:
            raise ValueError(f"Unsupported pooling mode: {pooling}")
        self.pooling = pooling
        lstm_dropout = dropout if num_layers > 1 else 0.0
        self.encoder = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=lstm_dropout,
            batch_first=True,
        )
        pooled_size = hidden_size * 2 if pooling == "last_mean" else hidden_size
        self.head = nn.Sequential(
            nn.LayerNorm(pooled_size),
            nn.Linear(pooled_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        encoded, _ = self.encoder(x)
        pooled = pool_sequence(encoded, self.pooling)
        return self.head(pooled)


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 512) -> None:
        super().__init__()
        position = torch.arange(max_len, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float32) * (-math.log(10000.0) / d_model)
        )
        pe = torch.zeros(max_len, d_model, dtype=torch.float32)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0), persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1)]


class TransformerRegressor(nn.Module):
    def __init__(
        self,
        input_size: int,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dropout: float = 0.1,
        pooling: str = "last",
    ) -> None:
        super().__init__()
        if pooling not in {"last", "mean", "last_mean"}:
            raise ValueError(f"Unsupported pooling mode: {pooling}")
        self.pooling = pooling
        self.input_proj = nn.Linear(input_size, d_model)
        self.positional = PositionalEncoding(d_model=d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        pooled_size = d_model * 2 if pooling == "last_mean" else d_model
        self.head = nn.Sequential(
            nn.LayerNorm(pooled_size),
            nn.Linear(pooled_size, d_model),
            nn.GELU(),
            nn.Linear(d_model, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        projected = self.input_proj(x)
        encoded = self.encoder(self.positional(projected))
        pooled = pool_sequence(encoded, self.pooling)
        return self.head(pooled)


def pool_sequence(encoded: torch.Tensor, pooling: str) -> torch.Tensor:
    if pooling == "last":
        return encoded[:, -1, :]
    if pooling == "mean":
        return encoded.mean(dim=1)
    if pooling == "last_mean":
        return torch.cat([encoded[:, -1, :], encoded.mean(dim=1)], dim=-1)
    raise ValueError(f"Unsupported pooling mode: {pooling}")


def build_sequence_model(
    model_name: str,
    input_size: int,
    hidden_size: int = 64,
    num_layers: int = 2,
    dropout: float = 0.1,
    nhead: int = 4,
    pooling: str = "last",
) -> nn.Module:
    if model_name == "lstm":
        return LSTMRegressor(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            pooling=pooling,
        )
    if model_name == "transformer":
        if hidden_size % nhead != 0:
            raise ValueError(f"Transformer hidden_size must be divisible by nhead, got {hidden_size} and {nhead}")
        return TransformerRegressor(
            input_size=input_size,
            d_model=hidden_size,
            nhead=nhead,
            num_layers=num_layers,
            dropout=dropout,
            pooling=pooling,
        )
    raise ValueError(f"Unknown sequence model: {model_name}")
