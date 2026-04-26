# Baseline Training Notes

This task trains the first benchmark models on the processed dataset.

## Included Models
- persistence
- moving_average
- linear_regression
- ridge
- cpu_heuristic
- random_forest

## Expected Input
- `data/processed/<version>/train.parquet`
- `data/processed/<version>/val.parquet`
- `data/processed/<version>/test.parquet`

## Usage
```powershell
python src/training/train_baselines.py `
  --dataset-dir data/processed/v1 `
  --output-dir reports/benchmarks/v1
```

## Outputs
- `reports/benchmarks/<version>/benchmark.csv`
- `reports/benchmarks/<version>/benchmark.json`
- `reports/benchmarks/<version>/summary.md`

## Dependency Notes
- Required now: `pandas`, `numpy`, `scikit-learn`
- Optional later: `xgboost` or `lightgbm`
- `torch` is not required for this task

## Deep Learning Task

When the project reaches `04-24-train-deep-models`, use:

```powershell
python src/training/train_deep_models.py `
  --dataset-dir data/processed/v1 `
  --output-dir reports/deep-models/v1 `
  --model lstm
```

Recommended defaults now include:
- feature / target standardization from the train split
- validation and test sequence windows that inherit context from earlier splits
- early stopping with `epochs=80`, `patience=12`, `min_epochs=20`
- `batch_size=32`, `weight_decay=1e-4`, `grad_clip=1.0`
- configurable sequence `feature_set` values: `legacy`, `cyclic`, `compact`, `enhanced`
- configurable sequence pooling: `last`, `mean`, `last_mean`

For the current tuned run, use:

```powershell
python src/training/train_deep_models.py `
  --dataset-dir data/processed/v1 `
  --output-dir reports/deep-models/v1_tuned `
  --model lstm
```

Best-known LSTM recipe so far:

```powershell
python src/training/train_deep_models.py `
  --dataset-dir data/processed/v1 `
  --output-dir reports/deep-models/best-lstm-residual `
  --model lstm `
  --target-mode residual `
  --num-layers 1 `
  --hidden-size 96
```

Current best LSTM result:
- test_mae: `0.003703522961586714`
- test_rmse: `0.004624821547512608`
- test_r2: `0.9249907721285076`

Seed stability check for `hidden_size=96`:
- seed `42`: `0.00370 / 0.00462 / 0.92499`
- seed `7`: `0.00416 / 0.00488 / 0.91657`
- seed `21`: `0.00437 / 0.00513 / 0.90782`

Across these three seeds, the mean metrics are `0.00408 / 0.00488 / 0.91646`, which is effectively tied with the current `random_forest` baseline.

Repeated-run comparison against `random_forest` is recorded at:
- `reports/comparisons/repeated-runs/lstm_residual_h96_vs_random_forest.md`

Note:
- a follow-up `scheduler=plateau` retry on the same seeds did not change the best-checkpoint outcomes for this setup
- a regularization follow-up found `weight_decay=1e-3` slightly improves the repeated-run mean, while `dropout` does not matter for the current `num_layers=1` LSTM
- a conservative early-stopping follow-up (`patience=20/30`, `min_epochs=30/40`) did not move the best checkpoint away from epoch `7`

Deep learning dependencies:
- `torch`
- `pandas`
- `numpy`

Sequence ensemble evaluation is now available with:

```powershell
python src/training/evaluate_sequence_ensemble.py `
  --dataset-dir data/processed/v1 `
  --output-dir reports/comparisons/repeated-runs/lstm_residual_h96_wd1e3_ensemble `
  --name lstm_residual_h96_wd1e3_ensemble `
  --checkpoint reports/deep-models/regularization/lstm_residual_h96_seed42_wd1e3/lstm_best.pt `
  --checkpoint reports/deep-models/regularization/lstm_residual_h96_wd1e3_seed7/lstm_best.pt `
  --checkpoint reports/deep-models/regularization/lstm_residual_h96_wd1e3_seed21/lstm_best.pt
```

Current 3-member ensemble result on the test split:
- ensemble test_mae: `0.004013902973383665`
- ensemble test_rmse: `0.004764464303393069`
- ensemble test_r2: `0.9203927027788574`

Compared with the repeated-run `random_forest` mean:
- MAE is still slightly worse
- RMSE and R2 are now slightly better
- run averaging is therefore useful for stability, but not yet a clean across-the-board baseline win

Loss / normalization follow-up:
- `HuberLoss(delta=1.0)` was slightly worse than the current `MSELoss` control
- `HuberLoss(delta=0.5)` was worse again
- disabling target standardization (`target_scaling=none`) was clearly harmful and pushed the best checkpoint to the final epoch
- the best known single-model setup still remains `MSE + standard target scaling + weight_decay=1e-3`

`v2` holdout repeated-run validation is available with:

```powershell
& 'C:\Users\22208\anaconda3\envs\dc-energy\python.exe' src/training/run_holdout_stability.py `
  --train-config configs/deep-learning/lstm-residual-v2-best.json `
  --holdout-path data/processed/v2_holdout_pdu/full.parquet `
  --output-dir reports/comparisons/v2_holdout_repeated `
  --seed 42 `
  --seed 7 `
  --seed 21 `
  --baseline-model random_forest
```

Repeated-run outputs:
- `reports/comparisons/v2_holdout_repeated/stability_metrics.csv`
- `reports/comparisons/v2_holdout_repeated/stability_metrics.json`
- `reports/comparisons/v2_holdout_repeated/stability_summary.md`

`v2` holdout ensemble evaluation is available with:

```powershell
& 'C:\Users\22208\anaconda3\envs\dc-energy\python.exe' src/training/evaluate_sequence_ensemble.py `
  --holdout-path data/processed/v2_holdout_pdu/full.parquet `
  --output-dir reports/comparisons/v2_holdout_repeated/lstm_ensemble_holdout `
  --split holdout `
  --name v2_holdout_lstm_residual_h96_wd1e3_ensemble `
  --checkpoint reports/comparisons/v2_holdout_repeated/deep-models/seed42/lstm_best.pt `
  --checkpoint reports/comparisons/v2_holdout_repeated/deep-models/seed7/lstm_best.pt `
  --checkpoint reports/comparisons/v2_holdout_repeated/deep-models/seed21/lstm_best.pt
```

Holdout ensemble outputs:
- `reports/comparisons/v2_holdout_repeated/lstm_ensemble_holdout/ensemble_metrics.json`
- `reports/comparisons/v2_holdout_repeated/lstm_ensemble_holdout/ensemble_summary.md`

Current best generalized `v2` recipe is the `last_mean` pooling follow-up:

```powershell
& 'C:\Users\22208\anaconda3\envs\dc-energy\python.exe' src/training/run_holdout_stability.py `
  --train-config configs/deep-learning/lstm-residual-v2-last-mean.json `
  --holdout-path data/processed/v2_holdout_pdu_opt/full.parquet `
  --output-dir reports/comparisons/v2_holdout_repeated_last_mean `
  --seed 42 `
  --seed 7 `
  --seed 21 `
  --baseline-model random_forest
```

Generalization summary for `last_mean`:
- repeated holdout mean: `0.0031159091 / 0.0044552966 / 0.9910355092`
- previous repeated holdout mean: `0.0037102647 / 0.0050186245 / 0.9886073640`
- repeated test mean is slightly worse than the old `last` head, but holdout generalization is materially better

`last_mean` ensemble evaluation is available with:

```powershell
& 'C:\Users\22208\anaconda3\envs\dc-energy\python.exe' src/training/evaluate_sequence_ensemble.py `
  --holdout-path data/processed/v2_holdout_pdu_opt/full.parquet `
  --output-dir reports/comparisons/v2_holdout_repeated_last_mean/lstm_ensemble_holdout `
  --split holdout `
  --name v2_holdout_lstm_legacy_last_mean_ensemble `
  --checkpoint reports/comparisons/v2_holdout_repeated_last_mean/deep-models/seed42/lstm_best.pt `
  --checkpoint reports/comparisons/v2_holdout_repeated_last_mean/deep-models/seed7/lstm_best.pt `
  --checkpoint reports/comparisons/v2_holdout_repeated_last_mean/deep-models/seed21/lstm_best.pt
```

Flex-enhanced follow-up:
- packaged flexibility windows are available under `data/processed/google_flex_windows_v1`
- merged datasets are available under `data/processed/v2_expanded_dev_flex` and `data/processed/v2_holdout_pdu_flex`
- the current strongest unseen-PDU `v2` setup is the flex-enhanced `last_mean` LSTM

Run the flex-enhanced repeated holdout validation with:

```powershell
& 'C:\Users\22208\anaconda3\envs\dc-energy\python.exe' src/training/run_holdout_stability.py `
  --train-config configs/deep-learning/lstm-residual-v2-flex-last-mean.json `
  --holdout-path data/processed/v2_holdout_pdu_flex/full.parquet `
  --output-dir reports/comparisons/v2_holdout_repeated_flex_last_mean `
  --seed 42 `
  --seed 7 `
  --seed 21 `
  --baseline-model random_forest
```

Current flex-enhanced repeated result:
- test mean: `0.0026197596 / 0.0032828317 / 0.9939579362`
- holdout mean: `0.0026618235 / 0.0039473265 / 0.9929653942`
- this is worse on the in-domain test split, but substantially better on the unseen-PDU holdout than the non-flex `last_mean` control

Flex-enhanced holdout ensemble:

```powershell
& 'C:\Users\22208\anaconda3\envs\dc-energy\python.exe' src/training/evaluate_sequence_ensemble.py `
  --holdout-path data/processed/v2_holdout_pdu_flex/full.parquet `
  --output-dir reports/comparisons/v2_holdout_repeated_flex_last_mean/lstm_ensemble_holdout `
  --split holdout `
  --name v2_holdout_lstm_flex_last_mean_ensemble `
  --checkpoint reports/comparisons/v2_holdout_repeated_flex_last_mean/deep-models/seed42/lstm_best.pt `
  --checkpoint reports/comparisons/v2_holdout_repeated_flex_last_mean/deep-models/seed7/lstm_best.pt `
  --checkpoint reports/comparisons/v2_holdout_repeated_flex_last_mean/deep-models/seed21/lstm_best.pt
```

`v3` cross-cell holdout repeated-run validation is available with:

```powershell
& 'C:\Users\22208\anaconda3\envs\dc-energy\python.exe' src/training/run_holdout_stability.py `
  --train-config configs/deep-learning/lstm-residual-v3-cell-e-best.json `
  --holdout-path data/processed/v3_cell_e_holdout_pdu/full.parquet `
  --output-dir reports/comparisons/v3_cell_e_holdout_repeated `
  --seed 42 `
  --seed 7 `
  --seed 21 `
  --baseline-model random_forest
```

Cross-cell repeated-run outputs:
- `reports/comparisons/v3_cell_e_holdout_repeated/stability_metrics.csv`
- `reports/comparisons/v3_cell_e_holdout_repeated/stability_metrics.json`
- `reports/comparisons/v3_cell_e_holdout_repeated/stability_summary.md`

`v3` holdout ensemble evaluation is available with:

```powershell
& 'C:\Users\22208\anaconda3\envs\dc-energy\python.exe' src/training/evaluate_sequence_ensemble.py `
  --holdout-path data/processed/v3_cell_e_holdout_pdu/full.parquet `
  --output-dir reports/comparisons/v3_cell_e_holdout_repeated/lstm_ensemble_holdout `
  --split holdout `
  --name v3_cell_e_holdout_lstm_residual_h96_wd1e3_ensemble `
  --checkpoint reports/comparisons/v3_cell_e_holdout_repeated/deep-models/seed42/lstm_best.pt `
  --checkpoint reports/comparisons/v3_cell_e_holdout_repeated/deep-models/seed7/lstm_best.pt `
  --checkpoint reports/comparisons/v3_cell_e_holdout_repeated/deep-models/seed21/lstm_best.pt
```

Cross-cell holdout ensemble outputs:
- `reports/comparisons/v3_cell_e_holdout_repeated/lstm_ensemble_holdout/ensemble_metrics.json`
- `reports/comparisons/v3_cell_e_holdout_repeated/lstm_ensemble_holdout/ensemble_summary.md`

`v4` third external-validation repeated-run is available with:

```powershell
& 'C:\Users\22208\anaconda3\envs\dc-energy\python.exe' src/training/run_holdout_stability.py `
  --train-config configs/deep-learning/lstm-residual-v4-cell-b-best.json `
  --holdout-path data/processed/v4_cell_b_holdout_pdu/full.parquet `
  --output-dir reports/comparisons/v4_cell_b_holdout_repeated `
  --seed 42 `
  --seed 7 `
  --seed 21 `
  --baseline-model random_forest
```

Third external-validation outputs:
- `reports/comparisons/v4_cell_b_holdout_repeated/stability_metrics.csv`
- `reports/comparisons/v4_cell_b_holdout_repeated/stability_metrics.json`
- `reports/comparisons/v4_cell_b_holdout_repeated/stability_summary.md`

`v4` holdout ensemble evaluation is available with:

```powershell
& 'C:\Users\22208\anaconda3\envs\dc-energy\python.exe' src/training/evaluate_sequence_ensemble.py `
  --holdout-path data/processed/v4_cell_b_holdout_pdu/full.parquet `
  --output-dir reports/comparisons/v4_cell_b_holdout_repeated/lstm_ensemble_holdout `
  --split holdout `
  --name v4_cell_b_holdout_lstm_residual_h96_wd1e3_ensemble `
  --checkpoint reports/comparisons/v4_cell_b_holdout_repeated/deep-models/seed42/lstm_best.pt `
  --checkpoint reports/comparisons/v4_cell_b_holdout_repeated/deep-models/seed7/lstm_best.pt `
  --checkpoint reports/comparisons/v4_cell_b_holdout_repeated/deep-models/seed21/lstm_best.pt
```

Third external-validation ensemble outputs:
- `reports/comparisons/v4_cell_b_holdout_repeated/lstm_ensemble_holdout/ensemble_metrics.json`
- `reports/comparisons/v4_cell_b_holdout_repeated/lstm_ensemble_holdout/ensemble_summary.md`

## Compare Baseline vs Deep Models

After the deep-model runs finish, combine the benchmark outputs with:

```powershell
python src/training/compare_model_benchmarks.py `
  --baseline-json reports/benchmarks/v1/benchmark.json `
  --deep-dir reports/deep-models/v1_tuned `
  --output-dir reports/comparisons/v1_tuned
```

Comparison outputs:
- `reports/comparisons/<version>/comparison.csv`
- `reports/comparisons/<version>/comparison.json`
- `reports/comparisons/<version>/comparison_summary.md`
