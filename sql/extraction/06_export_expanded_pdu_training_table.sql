-- Purpose: export a larger multi-PDU training table after candidate ranking.
-- This script is intended to run directly in the BigQuery console.
-- Replace target_pdus after running validation/04_rank_pdu_candidates.sql.
--
-- Current ready-to-run development export:
-- 1) development PDUs: pdu20, pdu21, pdu22, pdu23, pdu24
-- 2) holdout PDUs are exported separately in 07_export_holdout_pdu_training_table.sql
-- 3) time range: window_index 1500-2100

DECLARE target_cell STRING DEFAULT 'f';
DECLARE target_pdus ARRAY<STRING> DEFAULT [
  'pdu20',
  'pdu21',
  'pdu22',
  'pdu23',
  'pdu24'
];
DECLARE min_window_index INT64 DEFAULT 1500;
DECLARE max_window_index INT64 DEFAULT 2100;

WITH target_machines AS (
  SELECT
    machine_id,
    pdu,
    cell
  FROM `google.com:google-cluster-data.powerdata_2019.machine_to_pdu_mapping`
  WHERE cell = target_cell
    AND pdu IN UNNEST(target_pdus)
),
usage_5m AS (
  SELECT
    tm.cell,
    tm.pdu,
    CAST(FLOOR(u.start_time / 300000000.0) AS INT64) AS window_index,
    COUNT(*) AS instance_count,
    COUNT(DISTINCT u.collection_id) AS collection_count,
    COUNT(DISTINCT u.machine_id) AS machine_count,
    SUM(u.average_usage.cpus) AS total_cpu_usage,
    AVG(u.average_usage.cpus) AS avg_cpu_usage,
    MAX(u.average_usage.cpus) AS max_cpu_usage
  FROM `google.com:google-cluster-data.clusterdata_2019_f.instance_usage` AS u
  JOIN target_machines AS tm
    ON u.machine_id = tm.machine_id
  WHERE CAST(FLOOR(u.start_time / 300000000.0) AS INT64) BETWEEN min_window_index AND max_window_index
    AND (u.alloc_collection_id IS NULL OR u.alloc_collection_id = 0)
  GROUP BY 1, 2, 3
),
power_5m AS (
  SELECT
    cell,
    pdu,
    CAST(FLOOR(time / 300000000.0) AS INT64) AS window_index,
    TIMESTAMP_MICROS(CAST(FLOOR(time / 300000000.0) AS INT64) * 300000000) AS window_start,
    AVG(measured_power_util) AS measured_power_util,
    AVG(production_power_util) AS production_power_util
  FROM `google.com:google-cluster-data.powerdata_2019.cellf_*`
  WHERE _TABLE_SUFFIX IN UNNEST(target_pdus)
    AND NOT bad_measurement_data
    AND NOT bad_production_power_data
    AND CAST(FLOOR(time / 300000000.0) AS INT64) BETWEEN min_window_index AND max_window_index
  GROUP BY 1, 2, 3, 4
)
SELECT
  p.window_start,
  p.cell,
  p.pdu,
  p.measured_power_util,
  p.production_power_util,
  COALESCE(u.instance_count, 0) AS instance_count,
  COALESCE(u.collection_count, 0) AS collection_count,
  COALESCE(u.machine_count, 0) AS machine_count,
  COALESCE(u.total_cpu_usage, 0) AS total_cpu_usage,
  COALESCE(u.avg_cpu_usage, 0) AS avg_cpu_usage,
  COALESCE(u.max_cpu_usage, 0) AS max_cpu_usage
FROM power_5m AS p
LEFT JOIN usage_5m AS u
  USING (cell, pdu, window_index)
ORDER BY p.cell, p.pdu, p.window_start;
