# Three-Round External Validation Summary (2026-04-26)

## Scope

This summary compares the three strongest external holdout validations completed so far:

1. `cell=f` unseen-PDU holdout
2. `cell=e` cross-cell holdout
3. `cell=b` third external-validation holdout

## Repeated-Run LSTM vs Random Forest

| round | dev dataset | holdout dataset | LSTM holdout mean MAE | LSTM holdout mean RMSE | LSTM holdout mean R2 | RF holdout mean MAE | RF holdout mean RMSE | RF holdout mean R2 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `v2` | `data/processed/v2_expanded_dev` | `data/processed/v2_holdout_pdu/full.parquet` | `0.0037102647` | `0.0050186245` | `0.9886073640` | `0.0060610662` | `0.0087285977` | `0.9657566403` |
| `v3` | `data/processed/v3_cell_e_dev` | `data/processed/v3_cell_e_holdout_pdu/full.parquet` | `0.0032975996` | `0.0041938260` | `0.9933083234` | `0.0041824505` | `0.0052685854` | `0.9895525012` |
| `v4` | `data/processed/v4_cell_b_dev` | `data/processed/v4_cell_b_holdout_pdu/full.parquet` | `0.0030404069` | `0.0038973598` | `0.9743562430` | `0.0038785667` | `0.0049205475` | `0.9590908819` |

## Winner Counts vs Random Forest

| round | MAE wins | RMSE wins | R2 wins |
|---|---:|---:|---:|
| `v2` | `3 / 3` | `3 / 3` | `3 / 3` |
| `v3` | `3 / 3` | `3 / 3` | `3 / 3` |
| `v4` | `3 / 3` | `3 / 3` | `3 / 3` |

## Ensemble Holdout Results

| round | ensemble MAE | ensemble RMSE | ensemble R2 |
|---|---:|---:|---:|
| `v2` | `0.0036813214` | `0.0049790579` | `0.9888077557` |
| `v3` | `0.0032374905` | `0.0041258109` | `0.9935250758` |
| `v4` | `0.0029996755` | `0.0038512212` | `0.9749633744` |

## Current Interpretation

- The residual LSTM has now beaten `random_forest` on three separate external holdout configurations.
- The advantage remains stable across repeated seeds in all three rounds.
- Simple three-member run averaging improves all three holdout setups further.
- This is now materially stronger evidence that the model is learning transferable structure across different PDU groups and across multiple cells, not only the original `cell=f` slice.
