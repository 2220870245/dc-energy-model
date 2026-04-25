# LSTM Narrow Ablation Summary

## Search Scope

- fixed setup: `target_mode=residual`, `context_length=12`, `num_layers=1`
- tested capacity: `hidden_size=48`, `80`, `96`
- tested seeds on best capacity: `42`, `7`, `21`

## Capacity Results

| variant | test_mae | test_rmse | test_r2 |
|---|---:|---:|---:|
| `hidden_size=48` | `0.003844082821160555` | `0.004606299469137` | `0.9255903858321652` |
| `hidden_size=80` | `0.004164777230471373` | `0.004940135689628282` | `0.9144140466142731` |
| `hidden_size=96` | `0.003703522961586714` | `0.004624821547512608` | `0.9249907721285076` |

## Seed Stability for `hidden_size=96`

| seed | test_mae | test_rmse | test_r2 |
|---|---:|---:|---:|
| `42` | `0.003703522961586714` | `0.004624821547512608` | `0.9249907721285076` |
| `7` | `0.0041618021205067635` | `0.004877615189174948` | `0.9165666310467611` |
| `21` | `0.004369246307760477` | `0.005126984523779226` | `0.9078174422433474` |

Average across the three seeds:

- mean test_mae: `0.004078190463284652`
- mean test_rmse: `0.004876473753488928`
- mean test_r2: `0.9164582818062054`

## Takeaway

- Best observed run: `hidden_size=96`, `seed=42`
- Most important architectural choice remains `target_mode=residual` with `num_layers=1`
- Mean performance across seeds is essentially tied with the current `random_forest` baseline
- The next optimization pass should focus on variance reduction and fair repeated-run comparison, not larger context windows
