# V2 Holdout Ensemble vs Random Forest

## Setup

- holdout dataset: `data/processed/v2_holdout_pdu/full.parquet`
- LSTM members: `seed42`, `seed7`, `seed21`
- ensemble rule: mean prediction across the three saved checkpoints
- baseline reference: repeated-run `random_forest` mean across the same three seeds

## Metrics

| model | holdout_mae | holdout_rmse | holdout_r2 |
|---|---:|---:|---:|
| `lstm_member_mean` | `0.0037102646504839263` | `0.005018624468527059` | `0.9886073640160618` |
| `lstm_3_member_ensemble` | `0.003681321395561099` | `0.004979057892298793` | `0.9888077556755865` |
| `random_forest_mean` | `0.006061066198897377` | `0.008728597711900541` | `0.9657566402702695` |

## Interpretation

- The 3-member LSTM ensemble improves on the repeated-run single-model mean on all main holdout metrics.
- The ensemble remains clearly better than the repeated-run `random_forest` mean on MAE, RMSE, and R2.
- This means the `v2` holdout conclusion is not only stable across seeds, but can be strengthened further by simple run averaging.
