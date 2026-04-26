# SQL Extraction Workflow

This directory contains the first-pass BigQuery SQL templates for the Google cluster-data energy modeling project.

## Execution Order

1. `extraction/01_sample_power_trace.sql`
2. `extraction/02_machine_to_pdu_mapping.sql`
3. `extraction/03_instance_usage_join_pdu.sql`
4. `extraction/04_build_pdu_cpu_power_5min.sql`
5. `extraction/05_export_pdu_training_table.sql`
6. `validation/04_rank_pdu_candidates.sql`
7. `extraction/06_export_expanded_pdu_training_table.sql`
8. `extraction/07_export_holdout_pdu_training_table.sql`
9. `extraction/08_export_task_flexibility_trace.sql`
10. `extraction/09_export_flexibility_window_table.sql`
11. `validation/01_validate_power_range.sql`
12. `validation/02_validate_join_coverage.sql`
13. `validation/03_validate_multi_pdu_export_scope.sql`

## Notes

- These queries are based on the public examples from Google's `power_trace_analysis_colab.ipynb`.
- They are written as parameterized BigQuery scripts using `DECLARE` and `EXECUTE IMMEDIATE`.
- Before full-scale execution, run them on one cell, one PDU, and a short time range.
- Replace output table names and destination datasets to match your GCP project.
- `05_export_pdu_training_table.sql` is aligned with `src/data/dataset_contract.py`.
- Run `validation/03_validate_multi_pdu_export_scope.sql` before exporting a multi-PDU CSV.
- Use `validation/04_rank_pdu_candidates.sql` before any PDU expansion pass.
- See `EXPANSION_PLAN.md` for the recommended staged expansion workflow.
- `06_export_expanded_pdu_training_table.sql` is now prefilled with the current development PDU list.
- `07_export_holdout_pdu_training_table.sql` is prefilled with the current unseen-PDU holdout list.
- `08_export_task_flexibility_trace.sql` exports task-level scheduler metadata for flexibility modeling.
- `09_export_flexibility_window_table.sql` exports window-level flexibility summaries directly from BigQuery.

## Live Validation Status

Template status:
- Query templates created
- Directory structure created
- Validation SQL created

Pending:
- BigQuery authentication on the local machine
- Scan-cost recording
- Export verification with Parquet outputs
