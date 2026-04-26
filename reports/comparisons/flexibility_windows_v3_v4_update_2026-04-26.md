# Flexibility Windows v3/v4 Update: 2026-04-26

## Scope

Extended the same Google flexibility-window pipeline from `v2 cell=f` to:
- `v3 cell=e`
- `v4 cell=b`

New BigQuery exports:
- `data/raw/google_flex_windows_v3_cell_e_dev.csv`
- `data/raw/google_flex_windows_v3_cell_e_holdout.csv`
- `data/raw/google_flex_windows_v4_cell_b_dev.csv`
- `data/raw/google_flex_windows_v4_cell_b_holdout.csv`

Packaged datasets:
- `data/processed/google_flex_windows_v3_cell_e_dev`
- `data/processed/google_flex_windows_v3_cell_e_holdout`
- `data/processed/google_flex_windows_v4_cell_b_dev`
- `data/processed/google_flex_windows_v4_cell_b_holdout`

Merged model-ready datasets:
- `data/processed/v3_cell_e_dev_flex`
- `data/processed/v3_cell_e_holdout_pdu_flex`
- `data/processed/v4_cell_b_dev_flex`
- `data/processed/v4_cell_b_holdout_pdu_flex`

## Coverage

`v3 cell=e`
- development flex windows: `8004` rows, `4` PDUs, window range `1000-3000`
- holdout flex windows: `4002` rows, `2` PDUs, window range `1000-3000`

`v4 cell=b`
- development flex windows: `8004` rows, `4` PDUs, window range `1000-3000`
- holdout flex windows: `2001` rows, `1` PDU, window range `1000-3000`

## Join Coverage

Join coverage against the existing processed datasets:
- `v3_dev`: `8004 / 8004`
- `v3_holdout`: `2991 / 2991`
- `v4_dev`: `8004 / 8004`
- `v4_holdout`: `2001 / 2001`

Note:
- `v3` holdout flex windows contain `4002` rows because the BigQuery export keeps the full `1000-3000` window range for both PDUs
- the existing packaged `v3` holdout power dataset only uses `2991` of those keys
- the effective training/evaluation join is still complete

## Mean Flex Ratios

Window-level mean ratios:

- `v3_dev`: `flex=0.032222`, `critical=0.099264`, `online=0.868514`
- `v3_holdout`: `flex=0.033590`, `critical=0.103472`, `online=0.862938`
- `v4_dev`: `flex=0.043902`, `critical=0.111005`, `online=0.845094`
- `v4_holdout`: `flex=0.042002`, `critical=0.105643`, `online=0.852354`

## Status

The flexibility-window feature chain is now available for all three external-validation tracks:
- `v2 cell=f`
- `v3 cell=e`
- `v4 cell=b`

The next meaningful step is to train the flex-enhanced `last_mean` LSTM on:
- `v3_cell_e_dev_flex` with holdout `v3_cell_e_holdout_pdu_flex`
- `v4_cell_b_dev_flex` with holdout `v4_cell_b_holdout_pdu_flex`

That will show whether the `v2` holdout gain from flexibility features persists across cells.
