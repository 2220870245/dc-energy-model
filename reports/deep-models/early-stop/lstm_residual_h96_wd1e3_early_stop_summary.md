# Residual LSTM H96 WD1e-3 Early-Stopping Summary

## Fixed Setup

- `target_mode=residual`
- `context_length=12`
- `num_layers=1`
- `hidden_size=96`
- `weight_decay=1e-3`
- `seed=42`

## Tested Policies

| variant | patience | min_epochs | epochs_trained | best_epoch | test_mae | test_rmse | test_r2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| control | `12` | `20` | `20` | `7` | `0.0036510052159428596` | `0.004565171914039746` | `0.9269131917464354` |
| conservative A | `20` | `30` | `30` | `7` | `0.0036510052159428596` | `0.004565171914039746` | `0.9269131917464354` |
| conservative B | `30` | `40` | `40` | `7` | `0.0036510052159428596` | `0.004565171914039746` | `0.9269131917464354` |

## Takeaway

- More conservative early stopping did **not** change the best checkpoint
- The best validation epoch remained `7` in all cases
- Extending training only increased total epochs trained, not final test performance
- For this configuration, early-stopping conservatism is not the main source of seed variance
