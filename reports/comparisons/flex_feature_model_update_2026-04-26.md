# Flex Feature Model Update: 2026-04-26

## Setup

Control model:
- dataset: `v2_expanded_dev_opt`
- features: legacy sequence features
- pooling: `last_mean`

Flex-enhanced model:
- dataset: `v2_expanded_dev_flex`
- features: legacy sequence features + scheduler-derived flexibility features
- pooling: `last_mean`

Key new inputs:
- `online_cpu_usage`
- `flex_cpu_usage`
- `critical_cpu_usage`
- `deferrable_task_count`
- `critical_task_count`
- `mean_deferrable_slack_us`
- `mean_priority`
- `mean_scheduling_class`
- `flex_cpu_ratio`
- `critical_cpu_ratio`
- `online_cpu_ratio`

## Single-Seed Result

Seed `42` comparison:

| setup | test_mae | test_rmse | test_r2 | holdout_mae | holdout_rmse | holdout_r2 |
|---|---:|---:|---:|---:|---:|---:|
| control `legacy + last_mean` | 0.0020739350 | 0.0026978270 | 0.9959200147 | 0.0030544191 | 0.0043598400 | 0.9914184855 |
| flex `flex + last_mean` | 0.0026485522 | 0.0033059370 | 0.9938733995 | 0.0026658825 | 0.0039354475 | 0.9930078446 |

Interpretation:
- test split got worse
- unseen-PDU holdout got substantially better

## Repeated Holdout Result

Three-seed repeated evaluation:

| setup | test_mae_mean | test_rmse_mean | test_r2_mean | holdout_mae_mean | holdout_rmse_mean | holdout_r2_mean |
|---|---:|---:|---:|---:|---:|---:|
| control `legacy + last_mean` | 0.0021654676 | 0.0027835792 | 0.9956539473 | 0.0031159091 | 0.0044552966 | 0.9910355092 |
| flex `flex + last_mean` | 0.0026197596 | 0.0032828317 | 0.9939579362 | 0.0026618235 | 0.0039473265 | 0.9929653942 |

Holdout gain from flex features:
- `MAE`: `0.0031159091 -> 0.0026618235`
- `RMSE`: `0.0044552966 -> 0.0039473265`
- `R2`: `0.9910355092 -> 0.9929653942`

Stability:
- holdout `MAE` std dropped to `0.0000029453`
- holdout `RMSE` std dropped to `0.0000197326`
- holdout `R2` std dropped to `0.0000704503`

The flex-enhanced model still beats `random_forest` on holdout `MAE/RMSE/R2` for `3/3` seeds.

## Ensemble

Flex-enhanced 3-member holdout ensemble:
- `MAE = 0.0025988000`
- `RMSE = 0.0038902353`
- `R2 = 0.9931675793`

This is slightly better than the repeated single-model mean across all three holdout metrics.

## Conclusion

For this project stage, flexibility features should be treated as:
- harmful for same-distribution test fitting
- strongly beneficial for unseen-PDU holdout generalization

So if the project goal remains external generalization rather than in-domain fit, the flex-enhanced `last_mean` LSTM is currently the strongest `v2` model.
