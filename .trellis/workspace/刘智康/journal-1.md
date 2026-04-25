# Journal - 刘智康 (Part 1)

> AI development session journal
> Started: 2026-04-24

---



## Session 1: Cluster-Data Energy Modeling Setup

**Date**: 2026-04-24
**Task**: Cluster-Data Energy Modeling Setup

### Summary

Completed Trellis task breakdown, project guideline consolidation, SQL and training scaffold setup, and preparation of the `dc-energy` runtime environment.

### Main Changes

- Created a Trellis master roadmap task for the data center energy modeling project and split it into six executable subtasks with validation gates.
- Moved project-level scope and BigQuery access rules into `.trellis/spec/guides/energy-model-scope.md` and `.trellis/spec/guides/bigquery-access-checklist.md`.
- Started execution of sequential tasks instead of leaving only plans.
- Added SQL extraction scaffolding under `sql/` for power trace sampling, machine-to-PDU mapping, instance usage joins, PDU-level aggregation, and validation queries.
- Added dataset-building code under `src/data/` including dataset contracts, quality checks, a processed dataset builder, and dataset config.
- Added baseline training scaffolding under `src/models/`, `src/evaluation/`, and `src/training/` with unified metrics and benchmark output.
- Added deep learning scaffolding with PyTorch sequence dataset code, LSTM and Transformer model definitions, training entrypoint, and deep-learning config.
- Verified that all three main script entrypoints can be invoked from the dedicated `dc-energy` conda environment.
- Checked local tooling for Google Cloud access and confirmed that `gcloud` and `bq` are not installed yet, which is the current blocker for live BigQuery extraction.
- Inspected the new `dc-energy` environment, confirmed it initially lacked required packages, then installed and verified `numpy`, `pandas`, `pyarrow`, `scikit-learn`, `torch`, `xgboost`, and `lightgbm`.
- Confirmed that the package imports work correctly in `dc-energy`, including `torch 2.11.0+cpu`, and that this environment avoids the earlier OpenMP conflict seen in the base environment.
- Current active Trellis task is `.trellis/tasks/04-24-train-deep-models`, but actual data extraction and model runs remain blocked until Google Cloud CLI is installed and BigQuery access is configured.

### Git Commits

(No commits - planning session)

### Testing

- [OK] Script entrypoint smoke checks passed in `dc-energy`.
- [OK] Package import verification passed in `dc-energy`.

### Status

[OK] **Completed**

### Next Steps

- Install Google Cloud CLI and configure BigQuery access.


## Session 2: BigQuery Access, Multi-PDU Dataset Build, and Baseline Benchmark

**Date**: 2026-04-25
**Task**: BigQuery Access, Multi-PDU Dataset Build, and Baseline Benchmark

### Summary

Completed the first live BigQuery data-access pass, exported a contract-aligned multi-PDU sample dataset, built the first processed dataset version, and ran the baseline benchmark end to end.

### Main Changes

- Logged into Google Cloud CLI, configured proxy access, set an active project, and verified BigQuery connectivity from the local machine.
- Validated public Google cluster-data datasets and confirmed access to `clusterdata_2019_*`, `powerdata_2019`, and `machine_to_pdu_mapping`.
- Verified the power-table schema and the `instance_usage` schema, then worked through time-bucket alignment issues between cluster usage and power traces.
- Exported a first single-PDU validation sample, then corrected the export flow to produce a multi-PDU dataset covering `cell=f` with `pdu17`, `pdu18`, and `pdu19`.
- Built `data/processed/v1` from the corrected export with 864 rows total and 288 rows per PDU.
- Generated the dataset quality report and verified zero duplicate keys and zero missing rate on required columns.
- Ran baseline training on `data/processed/v1` and produced benchmark outputs under `reports/benchmarks/v1`.
- Updated SQL templates to better support contract-aligned multi-PDU exports and added an extra validation SQL for export-scope checks.
- Adjusted the random forest baseline to run with `n_jobs=1` to avoid the Windows multiprocessing permission failure seen in the current environment.

### Updated Files

- `sql/extraction/05_export_pdu_training_table.sql`
- `sql/validation/03_validate_multi_pdu_export_scope.sql`
- `sql/README.md`
- `src/models/baselines.py`
- `data/processed/v1/train.parquet`
- `data/processed/v1/val.parquet`
- `data/processed/v1/test.parquet`
- `data/processed/v1/metadata.json`
- `reports/data-quality/v1.md`
- `reports/benchmarks/v1/benchmark.csv`
- `reports/benchmarks/v1/benchmark.json`
- `reports/benchmarks/v1/summary.md`

### Testing

- [OK] BigQuery CLI connectivity test passed with `SELECT 1`.
- [OK] Public dataset access verified against `clusterdata_2019_a.machine_events`.
- [OK] Power and mapping tables verified in `powerdata_2019`.
- [OK] `build_training_dataset.py` completed successfully on the corrected multi-PDU export.
- [OK] `train_baselines.py` completed successfully on `data/processed/v1`.

### Results

- Final processed dataset version: `v1`
- Cells included: `f`
- PDUs included: `pdu17`, `pdu18`, `pdu19`
- Dataset split sizes: train `603`, val `129`, test `132`
- Best baseline model: `random_forest`
- Best baseline metrics: test MAE `0.0038355029222653853`, test RMSE `0.004876816530868513`, test R2 `0.9165939601951361`

### Status

[OK] **Completed**

### Next Steps

- Run deep-model training on `data/processed/v1`.
- Compare LSTM and Transformer results against the new baseline benchmark.
- Decide whether to expand the export window beyond the current 288-window multi-PDU sample.


## Session 3: Deep-Model Optimization, Expanded PDU Dataset, and Holdout Generalization

**Date**: 2026-04-25
**Task**: Deep-Model Optimization, Expanded PDU Dataset, and Holdout Generalization

### Summary

(Add summary)

### Main Changes

### Summary

Completed the full deep-model optimization pass, extended the dataset beyond the initial 3-PDU scope, and finished the first unseen-PDU generalization evaluation.

### Main Changes

- Tuned the sequence-model pipeline for residual forecasting with train-split standardization, inherited history context for val/test windows, stronger defaults, early stopping, and configurable model hyperparameters.
- Added sequence benchmark comparison tooling and ran LSTM / Transformer experiments against the baseline benchmark on `data/processed/v1`.
- Completed a focused LSTM ablation pass over `hidden_size`, `num_layers`, `learning_rate`, `seed`, `target_mode=residual`, scheduler options, regularization, and stopping behavior.
- Verified that `residual + num_layers=1 + hidden_size=96 + weight_decay=1e-3` is the strongest single-model configuration on the original `v1` dataset.
- Added sequence-ensemble evaluation tooling and confirmed that a 3-member residual-LSTM ensemble improves repeated-run metrics, though it was not yet a clean across-the-board win on the original `v1` comparison.
- Added loss / normalization experiment controls to the deep-learning trainer and verified that `MSE + standard target scaling` still beats the tested Huber and no-target-scaling variants.
- Designed a staged multi-PDU expansion plan for BigQuery, added candidate-ranking SQL, and created ready-to-run development and holdout export SQL templates.
- Read the BigQuery candidate-ranking output and selected `pdu20-24` as the next development PDUs plus `pdu17` and `pdu25` as unseen holdout PDUs.
- Built `data/processed/v2_expanded_dev` from the expanded development export and `data/processed/v2_holdout_pdu` as a `full_only` unseen-PDU evaluation dataset.
- Extended the dataset builder to support `split_mode=full_only` so holdout tables can be preserved for final external evaluation.
- Added holdout evaluation scripts for both baseline models and saved sequence checkpoints.
- Retrained baselines and the best residual LSTM on `v2_expanded_dev`, then evaluated both on `v2_holdout_pdu/full.parquet`.
- Confirmed that the tuned residual LSTM now clearly beats `random_forest` on unseen-PDU holdout performance, which is the strongest generalization result obtained so far.
- Backed up all of the above results to GitHub after each major milestone.

### Updated Files

- `src/data/sequence_dataset.py`
- `src/models/sequence_models.py`
- `src/models/baselines.py`
- `src/training/train_baselines.py`
- `src/training/train_deep_models.py`
- `src/training/compare_model_benchmarks.py`
- `src/training/evaluate_sequence_ensemble.py`
- `src/training/evaluate_baselines_holdout.py`
- `src/training/evaluate_sequence_holdout.py`
- `src/training/README.md`
- `src/data/build_training_dataset.py`
- `configs/deep-learning/default.json`
- `configs/deep-learning/lstm-residual-best.json`
- `sql/README.md`
- `sql/EXPANSION_PLAN.md`
- `sql/validation/04_rank_pdu_candidates.sql`
- `sql/extraction/06_export_expanded_pdu_training_table.sql`
- `sql/extraction/07_export_holdout_pdu_training_table.sql`
- `.trellis/tasks/04-24-train-deep-models/task.json`
- `data/processed/v2_expanded_dev/`
- `data/processed/v2_holdout_pdu/`
- `reports/deep-models/`
- `reports/comparisons/`
- `reports/benchmarks/`
- `reports/data-quality/`

### Testing

- [OK] `py_compile` checks passed for new and updated training / evaluation scripts.
- [OK] `train_baselines.py` completed successfully on `data/processed/v1` and `data/processed/v2_expanded_dev`.
- [OK] `train_deep_models.py` completed successfully across the main ablation, regularization, loss, and v2 retraining passes.
- [OK] `evaluate_sequence_ensemble.py` completed successfully on the 3-checkpoint residual-LSTM ensemble.
- [OK] `build_training_dataset.py` completed successfully for both `v2_expanded_dev` and `v2_holdout_pdu`.
- [OK] Holdout evaluation scripts completed successfully for both baselines and the saved LSTM checkpoint.

### Results

- Original best single-model `v1` residual LSTM: test MAE `0.0036510052159428596`, test RMSE `0.004565171914039746`, test R2 `0.9269131917464354`
- Original `v1` 3-member residual-LSTM ensemble: test MAE `0.004013902973383665`, test RMSE `0.004764464303393069`, test R2 `0.9203927027788574`
- Expanded development dataset: `data/processed/v2_expanded_dev` with `2983` rows (train `2078`, val `450`, test `455`)
- Unseen-PDU holdout dataset: `data/processed/v2_holdout_pdu/full.parquet` with `1132` rows
- `v2` best residual LSTM dev-test metrics: MAE `0.0021204082295298576`, RMSE `0.0027021152175776154`, R2 `0.99590703404911`
- `v2` random forest dev-test metrics: MAE `0.005244745450727983`, RMSE `0.008794527925699442`, R2 `0.956643376358224`
- Unseen-PDU holdout `random_forest`: MAE `0.006086088313678801`, RMSE `0.008717445055781486`, R2 `0.9658479824650014`
- Unseen-PDU holdout residual LSTM: MAE `0.003698076121509075`, RMSE `0.005011821217281058`, R2 `0.9886599759530615`

### Status

[OK] **Completed**

### Next Steps

- Decide whether to adopt the `v2` residual LSTM as the primary model.
- Optionally run a repeated-seed holdout stability check on `v2`.
- Package the v2 generalization results into the advisor-facing report and final project summary.


### Git Commits

| Hash | Message |
|------|---------|
| `de46d4f` | (see git log) |
| `dd6887a` | (see git log) |
| `31795b1` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete
