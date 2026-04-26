# Holdout Stability Summary

- deep_model: `lstm`
- seeds: 42, 7, 21
- holdout: `data/processed/v2_holdout_pdu_opt/full.parquet`
- python: `C:\Users\22208\anaconda3\envs\dc-energy\python.exe`

## Deep Model Aggregate

- test mean: `0.0021654676 / 0.0027835792 / 0.9956539473`
- test std: `0.0000808372 / 0.0000677791 / 0.0002112037`
- holdout mean: `0.0031159091 / 0.0044552966 / 0.9910355092`
- holdout std: `0.0000568889 / 0.0000826801 / 0.0003332083`

## Per-Seed Deep Model

| seed | best_epoch | test_mae | test_rmse | test_r2 | holdout_mae | holdout_rmse | holdout_r2 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 21 | 0.0020739350 | 0.0026978270 | 0.9959200147 | 0.0030544191 | 0.0043598400 | 0.9914184855 |
| 7 | 15 | 0.0021519186 | 0.0027893617 | 0.9956384578 | 0.0031017235 | 0.0044445439 | 0.9910817993 |
| 21 | 26 | 0.0022705493 | 0.0028635489 | 0.9954033695 | 0.0031915847 | 0.0045615059 | 0.9906062427 |

## Baseline Aggregate: `random_forest`

- test mean: `0.0053118011 / 0.0088873821 / 0.9557190252`
- test std: `0.0000834244 / 0.0000843007 / 0.0008412350`
- holdout mean: `0.0060610662 / 0.0087285977 / 0.9657566403`
- holdout std: `0.0000558031 / 0.0000931755 / 0.0007316931`

## Per-Seed Baseline: `random_forest`

| seed | test_mae | test_rmse | test_r2 | holdout_mae | holdout_rmse | holdout_r2 |
|---:|---:|---:|---:|---:|---:|---:|
| 7 | 0.0052612628 | 0.0088690522 | 0.9559054603 | 0.0061133733 | 0.0088478808 | 0.9648183301 |
| 21 | 0.0054293950 | 0.0089985663 | 0.9546082390 | 0.0059837370 | 0.0086204673 | 0.9666036083 |
| 42 | 0.0052447455 | 0.0087945279 | 0.9566433764 | 0.0060860883 | 0.0087174451 | 0.9658479825 |

## Winner Counts vs `random_forest`

- better MAE in `3` / `3` seeds
- better RMSE in `3` / `3` seeds
- better R2 in `3` / `3` seeds
