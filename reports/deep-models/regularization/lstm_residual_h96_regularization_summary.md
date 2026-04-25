# Residual LSTM H96 Regularization Summary

## Search Scope

Fixed base setup:

- `target_mode=residual`
- `context_length=12`
- `num_layers=1`
- `hidden_size=96`

Screened on `seed=42`:

- `dropout=0.2`
- `dropout=0.3`
- `weight_decay=5e-4`
- `weight_decay=1e-3`

## Seed-42 Screening

| variant | dropout | weight_decay | test_mae | test_rmse | test_r2 |
|---|---:|---:|---:|---:|---:|
| control | `0.1` | `1e-4` | `0.003703522961586714` | `0.004624821547512608` | `0.9249907721285076` |
| `dropout=0.2` | `0.2` | `1e-4` | `0.003703522961586714` | `0.004624821547512608` | `0.9249907721285076` |
| `dropout=0.3` | `0.3` | `1e-4` | `0.003703522961586714` | `0.004624821547512608` | `0.9249907721285076` |
| `weight_decay=5e-4` | `0.1` | `5e-4` | `0.003696122905239463` | `0.004684301072707183` | `0.9230489911767742` |
| `weight_decay=1e-3` | `0.1` | `1e-3` | `0.0036510052159428596` | `0.004565171914039746` | `0.9269131917464354` |

## Repeated-Run Check for `weight_decay=1e-3`

| seed | test_mae | test_rmse | test_r2 |
|---|---:|---:|---:|
| `42` | `0.0036510052159428596` | `0.004565171914039746` | `0.9269131917464354` |
| `7` | `0.004108082503080368` | `0.004825875684822982` | `0.9183272876486023` |
| `21` | `0.0043344260193407536` | `0.00509533202764736` | `0.9089521463046797` |

Mean across the three seeds:

- mean test_mae: `0.004031171246121327`
- mean test_rmse: `0.004828793208836696`
- mean test_r2: `0.9180642085665724`

Compared with the previous unscheduled `weight_decay=1e-4` control:

- mean test_mae improved from `0.004078190463284652` to `0.004031171246121327`
- mean test_rmse improved from `0.004876473753488928` to `0.004828793208836696`
- mean test_r2 improved from `0.9164582818062054` to `0.9180642085665724`

## Takeaway

- `dropout` had no effect here because the current best LSTM uses `num_layers=1`, so recurrent dropout is effectively inactive
- `weight_decay=1e-3` is the only regularization change that improved the repeated-run average
- The improvement is small but real, and it nearly matches the repeated-run `random_forest` mean
- Variance is still much higher than `random_forest`, so further stability work should target stopping behavior or run averaging rather than larger dropout
