# Model Optimization Update: 2026-04-26

## Summary

- Goal: improve external holdout generalization without changing the dataset scope.
- Winning change: keep the legacy feature set, but replace the sequence head from `pooling=last` to `pooling=last_mean`.
- Interpretation: the model now uses both the final hidden state and the mean hidden state across the context window, which improved unseen-PDU robustness.

## Feature Follow-up

Single-seed feature ablations on `v2_expanded_dev_opt`:

| setup | test_mae | test_rmse | test_r2 | note |
|---|---:|---:|---:|---|
| `legacy + last` | 0.0021204082 | 0.0027021152 | 0.9959070340 | control |
| `cyclic + last` | 0.0023514298 | 0.0030111963 | 0.9949171353 | worse |
| `compact + last` | 0.0021237049 | 0.0027804386 | 0.9956663183 | near tie, slightly worse |
| `enhanced + last` | 0.0026113563 | 0.0032880599 | 0.9939394806 | clearly worse |

Conclusion: broader engineered features did not help this setup.

## Architecture Follow-up

Single-seed structural ablations on `v2_expanded_dev_opt` with the legacy feature set:

| setup | test_mae | test_rmse | test_r2 | v2 holdout_mae | v2 holdout_rmse | v2 holdout_r2 |
|---|---:|---:|---:|---:|---:|---:|
| `legacy + last` | 0.0021204082 | 0.0027021152 | 0.9959070340 | 0.0036980761 | 0.0050118212 | 0.9886599760 |
| `legacy + mean` | 0.0022178576 | 0.0029148890 | 0.9952370675 | not promoted | not promoted | not promoted |
| `legacy + last_mean` | 0.0020739350 | 0.0026978270 | 0.9959200147 | 0.0030544191 | 0.0043598400 | 0.9914184855 |

Conclusion: `last_mean` is the clear winner.

## Repeated v2 Holdout

Repeated-seed comparison against the previous best `last` head:

| setup | holdout_mae_mean | holdout_rmse_mean | holdout_r2_mean | holdout_mae_std | holdout_rmse_std | holdout_r2_std |
|---|---:|---:|---:|---:|---:|---:|
| previous `last` | 0.0037102647 | 0.0050186245 | 0.9886073640 | 0.0002465391 | 0.0002197643 | 0.0009969820 |
| new `last_mean` | 0.0031159091 | 0.0044552966 | 0.9910355092 | 0.0000568889 | 0.0000826801 | 0.0003332083 |

Against `random_forest`, the `last_mean` model still wins `3/3` seeds on holdout `MAE`, `RMSE`, and `R2`.

## Ensemble Follow-up

On the same `v2` holdout:

| setup | mae | rmse | r2 |
|---|---:|---:|---:|
| previous 3-member `last` ensemble | 0.0036813214 | 0.0049790579 | 0.9888077557 |
| new 3-member `last_mean` ensemble | 0.0030950441 | 0.0044277021 | 0.9911492593 |

The new single model already beats the old ensemble, and the new ensemble improves a bit further.

## Cross-Cell Transfer Check

Using a `v2`-trained checkpoint directly on the `cell=e` and `cell=b` holdouts:

| setup | v3 holdout_mae | v3 holdout_rmse | v3 holdout_r2 | v4 holdout_mae | v4 holdout_rmse | v4 holdout_r2 |
|---|---:|---:|---:|---:|---:|---:|
| `legacy + last` | 0.0043915831 | 0.0053951769 | 0.9889279652 | 0.0053937174 | 0.0064171704 | 0.9304870083 |
| `legacy + last_mean` | 0.0039094281 | 0.0049016652 | 0.9908609017 | 0.0034511283 | 0.0044895499 | 0.9659760707 |

This is a transfer-style stress test, not a replacement for the cell-specific `v3` / `v4` training runs. It still shows the new head is materially more robust under distribution shift.
