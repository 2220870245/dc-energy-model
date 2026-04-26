# Cross-Cell Holdout Update (2026-04-26)

## Scope

- source cell: `e`
- development PDUs: `pdu26`, `pdu27`, `pdu30`, `pdu31`
- holdout PDUs: `pdu28`, `pdu29`
- export window: `1000-3000`

## Dataset Size

| dataset | rows |
|---|---:|
| `data/processed/v3_cell_e_dev` | `8004` |
| `data/processed/v3_cell_e_holdout_pdu/full.parquet` | `2991` |

## Repeated-Run Result

| model | holdout mean MAE | holdout mean RMSE | holdout mean R2 |
|---|---:|---:|---:|
| `lstm_residual_h96_wd1e3` | `0.0032975996` | `0.0041938260` | `0.9933083234` |
| `random_forest` | `0.0041824505` | `0.0052685854` | `0.9895525012` |

Winner count against `random_forest`:

- MAE: `3 / 3`
- RMSE: `3 / 3`
- R2: `3 / 3`

## Ensemble Result

| model | holdout_mae | holdout_rmse | holdout_r2 |
|---|---:|---:|---:|
| `lstm_member_mean` | `0.0032975996` | `0.0041938260` | `0.9933083234` |
| `lstm_3_member_ensemble` | `0.0032374905` | `0.0041258109` | `0.9935250758` |

## Comparison With Earlier Cell-F Holdout

Earlier `cell=f` holdout (`pdu17`, `pdu25`) repeated-run LSTM mean:

- MAE: `0.0037102647`
- RMSE: `0.0050186245`
- R2: `0.9886073640`

Current `cell=e` holdout repeated-run LSTM mean:

- MAE: `0.0032975996`
- RMSE: `0.0041938260`
- R2: `0.9933083234`

## Current Conclusion

- The residual LSTM still beats `random_forest` after moving to a new cell and a new unseen-PDU holdout split.
- The advantage is stable across repeated seeds and becomes slightly stronger with simple run averaging.
- This strengthens the claim that the model is learning transferable structure rather than only fitting the original `cell=f` slice.
