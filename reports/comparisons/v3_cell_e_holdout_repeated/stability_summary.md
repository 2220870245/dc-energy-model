# Holdout Stability Summary

- deep_model: `lstm`
- seeds: 42, 7, 21
- holdout: `data/processed/v3_cell_e_holdout_pdu/full.parquet`
- python: `C:\Users\22208\anaconda3\envs\dc-energy\python.exe`

## Deep Model Aggregate

- test mean: `0.0033138866 / 0.0043389560 / 0.9912656429`
- test std: `0.0001110191 / 0.0000915935 / 0.0003712882`
- holdout mean: `0.0032975996 / 0.0041938260 / 0.9933083234`
- holdout std: `0.0000628563 / 0.0000630247 / 0.0002015923`

## Per-Seed Deep Model

| seed | best_epoch | test_mae | test_rmse | test_r2 | holdout_mae | holdout_rmse | holdout_r2 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 2 | 0.0032396081 | 0.0042819189 | 0.9914975546 | 0.0033775377 | 0.0042773253 | 0.9930407790 |
| 7 | 6 | 0.0032312348 | 0.0042667564 | 0.9915576639 | 0.0032239587 | 0.0041250752 | 0.9935273845 |
| 21 | 9 | 0.0034708169 | 0.0044681927 | 0.9907417103 | 0.0032913024 | 0.0041790775 | 0.9933568066 |

## Baseline Aggregate: `random_forest`

- test mean: `0.0035725756 / 0.0045257768 / 0.9905012980`
- test std: `0.0000187761 / 0.0000228227 / 0.0000959424`
- holdout mean: `0.0041824505 / 0.0052685854 / 0.9895525012`
- holdout std: `0.0000254665 / 0.0000339947 / 0.0001345218`

## Per-Seed Baseline: `random_forest`

| seed | test_mae | test_rmse | test_r2 | holdout_mae | holdout_rmse | holdout_r2 |
|---:|---:|---:|---:|---:|---:|---:|
| 7 | 0.0035541167 | 0.0045046813 | 0.9905898812 | 0.0042000165 | 0.0052966225 | 0.9894414512 |
| 21 | 0.0035983357 | 0.0045574799 | 0.9903679998 | 0.0042008960 | 0.0052883885 | 0.9894742536 |
| 42 | 0.0035652743 | 0.0045151691 | 0.9905460129 | 0.0041464391 | 0.0052207453 | 0.9897417988 |

## Winner Counts vs `random_forest`

- better MAE in `3` / `3` seeds
- better RMSE in `3` / `3` seeds
- better R2 in `3` / `3` seeds
