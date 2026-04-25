# Repeated-Run Comparison: Residual LSTM vs Random Forest

## Setup

- dataset: `data/processed/v1`
- LSTM config: `target_mode=residual`, `context_length=12`, `num_layers=1`, `hidden_size=96`
- repeated seeds: `42`, `7`, `21`
- baseline model: `random_forest`

## Per-Seed Test Metrics

| model | seed | test_mae | test_rmse | test_r2 |
|---|---:|---:|---:|---:|
| `lstm_residual_h96` | `42` | `0.003703522961586714` | `0.004624821547512608` | `0.9249907721285076` |
| `lstm_residual_h96` | `7` | `0.0041618021205067635` | `0.004877615189174948` | `0.9165666310467611` |
| `lstm_residual_h96` | `21` | `0.004369246307760477` | `0.005126984523779226` | `0.9078174422433474` |
| `random_forest` | `42` | `0.0038355029222653853` | `0.004876816530868513` | `0.9165939601951361` |
| `random_forest` | `7` | `0.003832684082006597` | `0.004861265690037299` | `0.9171250304524871` |
| `random_forest` | `21` | `0.0037501001830280906` | `0.004754808993800291` | `0.9207150389615363` |

## Mean and Variance

| model | mean test_mae | mean test_rmse | mean test_r2 | std test_mae | std test_rmse | std test_r2 |
|---|---:|---:|---:|---:|---:|---:|
| `lstm_residual_h96` | `0.004078190463284652` | `0.004876473753488928` | `0.9164582818062054` | `0.00027813674733575335` | `0.00020500876540578464` | `0.007011401167839931` |
| `random_forest` | `0.0038060957291000245` | `0.0048309637382353676` | `0.9181446765363864` | `0.00003961155008345991` | `0.00005422247988684093` | `0.0018304063578027773` |

## Conclusion

- Best single run: `lstm_residual_h96` at seed `42`
- Mean performance across repeated runs still favors `random_forest`
- The LSTM's remaining gap is small in MAE/RMSE, but its variance is materially higher than the baseline
- The next optimization target is variance reduction and more robust training stability, not larger context windows

## Scheduler Follow-Up

A `ReduceLROnPlateau` retry with the same three seeds did **not** change any of the final metrics.

Reason:
- the best checkpoint was reached before the scheduler's first meaningful learning-rate reduction
- in this setup, the current early-stopping and best-checkpoint logic already locks in the same epoch

Implication:
- variance is not being driven by the lack of a plateau scheduler alone
- the next stability pass should target regularization and stopping behavior more directly
