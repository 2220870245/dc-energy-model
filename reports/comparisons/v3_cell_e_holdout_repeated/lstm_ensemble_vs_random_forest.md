# V3 Cell-E Holdout Ensemble vs Random Forest

## Setup

- development dataset: `data/processed/v3_cell_e_dev`
- holdout dataset: `data/processed/v3_cell_e_holdout_pdu/full.parquet`
- development PDUs: `pdu26`, `pdu27`, `pdu30`, `pdu31`
- holdout PDUs: `pdu28`, `pdu29`
- LSTM members: `seed42`, `seed7`, `seed21`
- baseline reference: repeated-run `random_forest` mean across the same three seeds

## Metrics

| model | holdout_mae | holdout_rmse | holdout_r2 |
|---|---:|---:|---:|
| `lstm_member_mean` | `0.00329759957579275` | `0.004193826003081092` | `0.9933083233726382` |
| `lstm_3_member_ensemble` | `0.0032374905422329903` | `0.004125810909402216` | `0.9935250757922173` |
| `random_forest_mean` | `0.00418245052039982` | `0.005268585434645834` | `0.9895525011902403` |

## Interpretation

- The 3-member LSTM ensemble improves on the repeated-run single-model mean on all main cross-cell holdout metrics.
- The ensemble also remains clearly better than the repeated-run `random_forest` mean on MAE, RMSE, and R2.
- This indicates the current residual LSTM path keeps its advantage not only within the earlier `cell=f` holdout, but also on the new `cell=e` cross-PDU holdout.
