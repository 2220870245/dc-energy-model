# Flexibility Windows Full-Scope Update: 2026-04-26

## Added

- BigQuery-side aggregated export:
  - `sql/extraction/09_export_flexibility_window_table.sql`
- Packager for aggregated window exports:
  - `src/flexibility/build_flexibility_dataset.py`
- Joiner from flex windows back into processed model datasets:
  - `src/flexibility/join_flex_features.py`

## Full Cell=f Development Scope

Packaged dataset:
- `data/processed/google_flex_windows_v1/flex_windows.parquet`

Coverage:
- rows: `3005`
- PDUs: `5`
- window range: `1500-2100`

Mean ratios:
- `flex_cpu_ratio = 0.055126`
- `critical_cpu_ratio = 0.084775`
- `online_cpu_ratio = 0.860099`

Per-PDU mean flex ratios:
- `pdu20 = 0.052565`
- `pdu21 = 0.053510`
- `pdu22 = 0.054908`
- `pdu23 = 0.053610`
- `pdu24 = 0.061038`

## Cell=f Holdout Scope

Packaged dataset:
- `data/processed/google_flex_windows_holdout_v1/flex_windows.parquet`

Coverage:
- rows: `1202`
- PDUs: `2`
- window range: `1500-2100`

Mean ratios:
- `flex_cpu_ratio = 0.057268`
- `critical_cpu_ratio = 0.083724`
- `online_cpu_ratio = 0.859009`

Per-PDU mean flex ratios:
- `pdu17 = 0.053748`
- `pdu25 = 0.060787`

## Join Readiness

The aggregated flexibility windows now align exactly with the current `v2` modeling scope:

- development join coverage: `2983 / 2983`
- holdout join coverage: `1132 / 1132`

Prepared merged datasets:
- `data/processed/v2_expanded_dev_flex`
- `data/processed/v2_holdout_pdu_flex`

These merged datasets add `20` flexibility features, including:
- `online_cpu_usage`
- `flex_cpu_usage`
- `critical_cpu_usage`
- `deferrable_task_count`
- `critical_task_count`
- `mean_deferrable_slack_us`
- `mean_scheduling_class`
- `flex_cpu_ratio`
- `critical_cpu_ratio`
- `online_cpu_ratio`

## Immediate Next Step

Train the current best `last_mean` LSTM on `v2_expanded_dev_flex` and compare:
- test split vs the current `v2` control
- unseen-PDU holdout vs the current `v2` control

That will answer whether scheduler-derived flexibility features actually improve power generalization.
