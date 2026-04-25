# Ensemble Comparison: Residual LSTM vs Random Forest

## Setup

- dataset: `data/processed/v1`
- LSTM members: `target_mode=residual`, `context_length=12`, `num_layers=1`, `hidden_size=96`, `weight_decay=1e-3`
- member seeds: `42`, `7`, `21`
- ensemble rule: mean of the three checkpoint predictions on the test split
- baseline reference: repeated-run `random_forest` mean across the same three seeds

## Test Metrics

| model | test_mae | test_rmse | test_r2 |
|---|---:|---:|---:|
| `lstm_member_mean` | `0.004031171246121327` | `0.004828793208836696` | `0.9180642085665726` |
| `lstm_3_member_ensemble` | `0.004013902973383665` | `0.004764464303393069` | `0.9203927027788574` |
| `random_forest_mean` | `0.0038060957291000245` | `0.0048309637382353676` | `0.9181446765363864` |

## Interpretation

- The 3-member LSTM ensemble improves on the repeated-run LSTM member mean for all main metrics.
- Relative to the repeated-run `random_forest` mean, the ensemble is still slightly worse on `test_mae`.
- On `test_rmse` and `test_r2`, the ensemble now edges past the repeated-run `random_forest` mean.
- This makes run averaging a useful stability tool for the current deep-model path, even though it does not produce a clean across-the-board win over the baseline.
