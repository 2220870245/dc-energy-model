# Training Dataset Build Notes

This task consumes the exported BigQuery join result and turns it into a versioned dataset for model training.

## Expected Input
- One parquet or csv file exported from the SQL workflow
- Required columns are defined in `src/data/dataset_contract.py`

## Output
- `data/processed/<version>/train.parquet`
- `data/processed/<version>/val.parquet`
- `data/processed/<version>/test.parquet`
- `data/processed/<version>/metadata.json`
- `reports/data-quality/<version>.md`

## First Usage
```powershell
python src/data/build_training_dataset.py `
  --input data/raw/bigquery_exports/pdu_training_table_v1.parquet `
  --output-dir data/processed/v1 `
  --report-path reports/data-quality/v1.md `
  --version v1
```

## Gate Status
- Gate 1: ready to validate once a real export file exists
- Gate 2: quality checks implemented in script output
- Gate 3: versioned outputs and metadata implemented
