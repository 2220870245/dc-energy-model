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
