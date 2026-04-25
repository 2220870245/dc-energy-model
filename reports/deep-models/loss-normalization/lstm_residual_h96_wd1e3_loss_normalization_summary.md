# Residual LSTM H96 Loss and Normalization Summary

## Setup

Fixed base setup:

- `model=lstm`
- `target_mode=residual`
- `context_length=12`
- `hidden_size=96`
- `num_layers=1`
- `weight_decay=1e-3`
- `seed=42`

Control reference:

- `loss=mse`
- `target_scaling=standard`
- test metrics: `0.0036510052159428596 / 0.004565171914039746 / 0.9269131917464354`

## Screening Results

| variant | loss | huber_delta | target_scaling | best_epoch | test_mae | test_rmse | test_r2 |
|---|---|---:|---|---:|---:|---:|---:|
| control | `mse` | `1.0` | `standard` | `7` | `0.0036510052159428596` | `0.004565171914039746` | `0.9269131917464354` |
| `huber_delta_1.0` | `huber` | `1.0` | `standard` | `7` | `0.0036844764836132526` | `0.004586706316154751` | `0.9262220478011414` |
| `huber_delta_0.5` | `huber` | `0.5` | `standard` | `7` | `0.0038482691161334515` | `0.004674963443051968` | `0.9233554693380309` |
| `target_scaling_none` | `mse` | `1.0` | `none` | `80` | `0.006290057674050331` | `0.007293703665792765` | `0.8134389628322763` |

## Takeaway

- In the current best residual-LSTM setup, `HuberLoss` does not improve over plain `MSELoss`.
- A smaller Huber delta makes the result worse, not more stable.
- Disabling target standardization is clearly harmful and also breaks the previous early-stop behavior by pushing the best checkpoint to the final epoch.
- The best known single-model setup therefore remains `MSE + standard target scaling + weight_decay=1e-3`.
