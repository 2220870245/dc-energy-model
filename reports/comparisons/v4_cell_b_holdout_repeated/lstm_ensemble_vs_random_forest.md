# V4 Cell-B Holdout Ensemble vs Random Forest

## Setup

- development dataset: `data/processed/v4_cell_b_dev`
- holdout dataset: `data/processed/v4_cell_b_holdout_pdu/full.parquet`
- development PDUs: `pdu11`, `pdu12`, `pdu13`, `pdu14`
- holdout PDU: `pdu15`
- LSTM members: `seed42`, `seed7`, `seed21`
- baseline reference: repeated-run `random_forest` mean across the same three seeds

## Metrics

| model | holdout_mae | holdout_rmse | holdout_r2 |
|---|---:|---:|---:|
| `lstm_member_mean` | `0.0030404068529605865` | `0.003897359781221158` | `0.974356242956421` |
| `lstm_3_member_ensemble` | `0.0029996754601597786` | `0.0038512212337513214` | `0.9749633743590086` |
| `random_forest_mean` | `0.0038785667339825275` | `0.00492054746698218` | `0.9590908819274497` |

## Interpretation

- The 3-member LSTM ensemble improves on the repeated-run single-model mean on all main holdout metrics.
- The ensemble remains clearly better than the repeated-run `random_forest` mean on MAE, RMSE, and R2.
- This provides a third external-validation pass in which the residual LSTM still keeps a stable holdout advantage.
