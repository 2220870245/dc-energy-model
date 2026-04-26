# Holdout Stability Summary

- deep_model: `lstm`
- seeds: 42, 7, 21
- holdout: `data/processed/v4_cell_b_holdout_pdu/full.parquet`
- python: `C:\Users\22208\anaconda3\envs\dc-energy\python.exe`

## Deep Model Aggregate

- test mean: `0.0034217692 / 0.0045648903 / 0.8436225037`
- test std: `0.0000450170 / 0.0000508358 / 0.0034932496`
- holdout mean: `0.0030404069 / 0.0038973598 / 0.9743562430`
- holdout std: `0.0000433310 / 0.0000464910 / 0.0006095691`

## Per-Seed Deep Model

| seed | best_epoch | test_mae | test_rmse | test_r2 | holdout_mae | holdout_rmse | holdout_r2 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 8 | 0.0034270722 | 0.0045436073 | 0.8450964768 | 0.0030581695 | 0.0039185109 | 0.9740808351 |
| 7 | 8 | 0.0034740604 | 0.0046350018 | 0.8388020454 | 0.0030823166 | 0.0039406970 | 0.9737865046 |
| 21 | 7 | 0.0033641749 | 0.0045160617 | 0.8469689889 | 0.0029807345 | 0.0038328714 | 0.9752013892 |

## Baseline Aggregate: `random_forest`

- test mean: `0.0034103786 / 0.0042741027 / 0.8629263731`
- test std: `0.0000097020 / 0.0000134736 / 0.0008645951`
- holdout mean: `0.0038785667 / 0.0049205475 / 0.9590908819`
- holdout std: `0.0000281812 / 0.0000379797 / 0.0006301562`

## Per-Seed Baseline: `random_forest`

| seed | test_mae | test_rmse | test_r2 | holdout_mae | holdout_rmse | holdout_r2 |
|---:|---:|---:|---:|---:|---:|---:|
| 7 | 0.0034038651 | 0.0042590624 | 0.8638907398 | 0.0039034624 | 0.0049573024 | 0.9584799162 |
| 21 | 0.0034240936 | 0.0042917545 | 0.8617932022 | 0.0038930713 | 0.0049360889 | 0.9588345055 |
| 42 | 0.0034031772 | 0.0042714914 | 0.8630951774 | 0.0038391666 | 0.0048682511 | 0.9599582241 |

## Winner Counts vs `random_forest`

- better MAE in `3` / `3` seeds
- better RMSE in `3` / `3` seeds
- better R2 in `3` / `3` seeds
