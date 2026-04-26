# Holdout Stability Summary

- deep_model: `lstm`
- seeds: 42, 7, 21
- holdout: `data/processed/v2_holdout_pdu_flex/full.parquet`
- python: `C:\Users\22208\anaconda3\envs\dc-energy\python.exe`

## Deep Model Aggregate

- test mean: `0.0026197596 / 0.0032828317 / 0.9939579362`
- test std: `0.0000404568 / 0.0000378266 / 0.0001386694`
- holdout mean: `0.0026618235 / 0.0039473265 / 0.9929653942`
- holdout std: `0.0000029453 / 0.0000197326 / 0.0000704503`

## Per-Seed Deep Model

| seed | best_epoch | test_mae | test_rmse | test_r2 | holdout_mae | holdout_rmse | holdout_r2 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 13 | 0.0026485522 | 0.0033059370 | 0.9938733995 | 0.0026658825 | 0.0039354475 | 0.9930078446 |
| 7 | 15 | 0.0026481813 | 0.0033130629 | 0.9938469597 | 0.0026606037 | 0.0039751344 | 0.9928661091 |
| 21 | 11 | 0.0025625455 | 0.0032294953 | 0.9941534493 | 0.0026589844 | 0.0039313974 | 0.9930222290 |

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
