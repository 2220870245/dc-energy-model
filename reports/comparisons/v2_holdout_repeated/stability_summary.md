# Holdout Stability Summary

- deep_model: `lstm`
- seeds: 42, 7, 21
- holdout: `data/processed/v2_holdout_pdu/full.parquet`
- python: `C:\Users\22208\anaconda3\envs\dc-energy\python.exe`

## Deep Model Aggregate

- test mean: `0.0021306073 / 0.0027209218 / 0.9958489654`
- test std: `0.0000359553 / 0.0000400001 / 0.0001225616`
- holdout mean: `0.0037102647 / 0.0050186245 / 0.9886073640`
- holdout std: `0.0002465391 / 0.0002197643 / 0.0009969820`

## Per-Seed Deep Model

| seed | best_epoch | test_mae | test_rmse | test_r2 | holdout_mae | holdout_rmse | holdout_r2 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 19 | 0.0021204082 | 0.0027021152 | 0.9959070340 | 0.0036980761 | 0.0050118212 | 0.9886599760 |
| 7 | 18 | 0.0021788480 | 0.0027765284 | 0.9956784990 | 0.0040181219 | 0.0052911168 | 0.9873608599 |
| 21 | 10 | 0.0020925656 | 0.0026841217 | 0.9959613631 | 0.0034145960 | 0.0047529354 | 0.9898012562 |

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
