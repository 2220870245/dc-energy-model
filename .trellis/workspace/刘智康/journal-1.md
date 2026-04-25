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
