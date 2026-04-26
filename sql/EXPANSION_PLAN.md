# Dataset Expansion Plan

## Goal

Expand beyond the current `v1` scope (`cell=f`, `pdu17-19`) without losing control over:

- coverage quality
- scan cost
- train/test comparability
- final generalization validation

## Recommended Strategy

### Stage A: Expand PDU Count Within the Same Cell

Reason:
- this is the cleanest way to increase data volume while keeping the environment stable
- it avoids mixing "more data" with "different cell distribution" too early

How:
1. Run `validation/04_rank_pdu_candidates.sql`
2. Keep only PDUs with:
   - `matched_ratio >= 0.95`
   - enough `matched_usage_windows`
3. Select:
   - `6-8` development PDUs for the next training dataset
   - `2-3` strong PDUs as unseen holdout PDUs

Recommended outcome:
- new development dataset: same `cell=f`, more PDUs, similar feature contract
- final external test: unseen PDUs from the same cell

### Stage B: Expand the Time Window

Reason:
- after Stage A, the next safest gain is more time coverage
- this tests temporal robustness without changing the object type

How:
1. Keep the same development PDU list
2. Widen the export range from the current narrow slice to a longer interval
3. Re-run quality checks and keep time-order splitting

### Stage C: Cross-PDU Holdout Evaluation

Reason:
- this is the strongest next validation after in-sample time splits
- it tells you whether the model learned transferable structure or only memorized seen PDUs

How:
1. Do not include the reserved holdout PDUs in the development export
2. Export them separately with the same feature contract
3. Evaluate the final model on this holdout-only table

## Console Execution Order

1. `sql/validation/04_rank_pdu_candidates.sql`
2. `sql/validation/03_validate_multi_pdu_export_scope.sql`
   Replace `target_pdus` with the chosen development PDU list.
3. `sql/extraction/06_export_expanded_pdu_training_table.sql`
4. Existing local dataset build and quality scripts

## Practical Recommendation For This Project

Do not jump directly from `3` PDUs to "all available PDUs".

Recommended next dataset:
- same cell: `f`
- development PDUs: `pdu20, pdu21, pdu22, pdu23, pdu24`
- holdout PDUs: `pdu17, pdu25`
- wider time range than current `1570-1857`

This gives you:
- more training rows
- a real unseen-PDU test
- less distribution shock than cross-cell expansion

## Cross-Cell Ranking Update (2026-04-26)

After the `cell=f` development + holdout pass was exhausted, a wider candidate scan was run across:

- time window: `1000-3000`
- cells: `a, b, c, d, e, g, h`

Strong candidates found:

- `cell=a`: `pdu10`, `pdu7`, `pdu9`, `pdu8`, `pdu6`
- `cell=b`: `pdu11`, `pdu12`, `pdu13`, `pdu14`, `pdu15`
- `cell=c`: `pdu41`, `pdu43`, `pdu42`
- `cell=d`: `pdu32`, `pdu36`, `pdu37`, `pdu35`, `pdu34`
- `cell=e`: `pdu26`, `pdu27`, `pdu30`, `pdu31`, `pdu29`, `pdu28`
- `cell=g`: `pdu2`, `pdu1`, `pdu5`
- `cell=h`: `pdu51`, `pdu52`, `pdu55`, `pdu46`, `pdu47`, `pdu50`, `pdu53`, `pdu54`

### Recommended Next Cross-Cell Target

Use `cell=e` first.

Reason:
- it has `6` strong candidates
- `5` of them have large window coverage (`1903+`)
- it supports a cleaner split than `cell=h`, whose extra candidates are much shorter (`520`, `414`, `320`)

Suggested split:

- development PDUs: `pdu26`, `pdu27`, `pdu30`, `pdu31`
- holdout PDUs: `pdu29`, `pdu28`
- recommended window range: `1000-3000`

Backup option:

- if a larger development set is preferred over a balanced holdout split, use `pdu29` as development and keep `pdu28` as the only holdout PDU

## Output Expectation

The expanded export should still match `src/data/dataset_contract.py`:

- `window_start`
- `cell`
- `pdu`
- `measured_power_util`
- `production_power_util`
- `instance_count`
- `collection_count`
- `machine_count`
- `total_cpu_usage`
- `avg_cpu_usage`
- `max_cpu_usage`
