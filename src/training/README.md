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

Deep learning dependencies:
- `torch`
- `pandas`
- `numpy`
