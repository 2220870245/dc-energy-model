# Flexibility Modeling Notes

This task turns Google task-level scheduler traces into `PDU x 5-minute window` flexibility summaries.

## Inputs

- A csv or parquet export produced from `sql/extraction/08_export_task_flexibility_trace.sql`
- For csv exports, the builder can now auto-skip the leading query echo that `bq query --format=csv` may prepend

## Outputs

- `task_trace.parquet`: task-level rows with derived lifecycle and state columns
- `flex_windows.parquet`: aggregated `base / flex / critical` proxy windows
- `metadata.json`
- a markdown quality report

For direct BigQuery aggregated exports, package the resulting csv with:

```powershell
python src/flexibility/build_flexibility_dataset.py `
  --input data/raw/google_flex_windows_v1.csv `
  --output-dir data/processed/google_flex_windows_v1 `
  --report-path reports/data-quality/google_flex_windows_v1.md `
  --version google_flex_windows_v1
```

To join the packaged flexibility windows back into an existing processed power dataset:

```powershell
python src/flexibility/join_flex_features.py `
  --dataset-dir data/processed/v2_expanded_dev `
  --flex-path data/processed/google_flex_windows_v1/flex_windows.parquet `
  --output-dir data/processed/v2_expanded_dev_flex `
  --report-path reports/data-quality/v2_expanded_dev_flex.md `
  --version v2_expanded_dev_flex
```

## First Usage

```powershell
python src/flexibility/build_flexibility_windows.py `
  --input data/raw/google_flex_trace_v1.csv `
  --output-dir data/processed/google_flex_v1 `
  --report-path reports/data-quality/google_flex_v1.md `
  --version google_flex_v1 `
  --rho 1.5 `
  --require-batch-scheduler
```

## Current Proxy Rules

- Flex candidate:
  - `collection_type == JOB`
  - `scheduling_class <= 1`
  - and optionally `preferred_scheduler == SCHEDULER_BATCH`
- Critical:
  - current window end plus one observed runtime exceeds the proxy deadline
- Deferrable:
  - flex candidate but not critical

These are explicit proxies, not ground-truth business deadlines.
