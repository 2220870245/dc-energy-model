# Flexibility Prototype Update: 2026-04-26

## What Was Added

- Task-level Google export SQL:
  - `sql/extraction/08_export_task_flexibility_trace.sql`
- Local builder for `PDU x 5-minute window` flexibility summaries:
  - `src/flexibility/build_flexibility_windows.py`
- Builder notes:
  - `src/flexibility/README.md`

## Prototype Run

Input trace:
- `data/raw/google_flex_trace_v1.csv`

Processed outputs:
- `data/processed/google_flex_v1_raw/task_trace.parquet`
- `data/processed/google_flex_v1_raw/flex_windows.parquet`
- `reports/data-quality/google_flex_v1_raw.md`

Proxy settings:
- `rho = 1.5`
- `max_flex_scheduling_class = 1`
- `require_batch_scheduler = true`

## Preliminary Result

Current prototype statistics:
- task rows: `200000`
- aggregated windows: `3`
- unique PDUs in the sample: `1`
- flex candidate ratio: `0.101900`
- deferrable ratio: `0.040015`
- critical ratio: `0.061885`
- mean window flex CPU ratio: `0.039121`
- mean window critical CPU ratio: `0.030588`

Window-level sample:
- `window_index=1500`: `flex_cpu_ratio=0.066400`, `critical_cpu_ratio=0.046129`
- `window_index=1501`: `flex_cpu_ratio=0.050961`, `critical_cpu_ratio=0.040754`
- `window_index=1502`: `flex_cpu_ratio=0.000001`, `critical_cpu_ratio=0.004881`

## Important Limitation

This is a prototype export, not the final full-scope flexibility dataset.

- The BigQuery csv export was capped at `--max_rows=200000`
- As a result, the current sample only covers the first `3` windows from `cell=f / pdu20`
- The pipeline itself is now validated end-to-end, but a production run should use either:
  - a narrower explicit query scope per shard, or
  - a larger export strategy than one single csv dump

## Immediate Next Step

Use the new export SQL in sharded mode:
- one `PDU` at a time, or
- one short window range at a time

Then merge the resulting parquet files and compute a stable flexibility summary over a longer horizon.
