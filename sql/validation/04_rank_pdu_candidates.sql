-- Purpose: rank candidate PDUs for dataset expansion inside one cell.
-- Run this in the BigQuery console first, then choose:
--   1) development PDUs with strong matched_ratio and enough windows
--   2) holdout PDUs for final generalization checks
--
-- Recommended first pass:
-- - keep target_cell = 'f'
-- - use a wider time range than v1
-- - require matched_ratio >= 0.95 for development PDUs
-- - reserve 2-3 strong PDUs as unseen holdout PDUs

DECLARE target_cell STRING DEFAULT 'f';
DECLARE min_window_index INT64 DEFAULT 1500;
DECLARE max_window_index INT64 DEFAULT 2100;

WITH target_machines AS (
  SELECT
    machine_id,
    cell,
    pdu
  FROM `google.com:google-cluster-data.powerdata_2019.machine_to_pdu_mapping`
  WHERE cell = target_cell
),
usage_windows AS (
  SELECT
    tm.pdu,
    CAST(FLOOR(u.start_time / 300000000.0) AS INT64) AS window_index
  FROM `google.com:google-cluster-data.clusterdata_2019_f.instance_usage` AS u
  JOIN target_machines AS tm
    ON u.machine_id = tm.machine_id
  WHERE CAST(FLOOR(u.start_time / 300000000.0) AS INT64) BETWEEN min_window_index AND max_window_index
  GROUP BY 1, 2
),
power_windows AS (
  SELECT
    pdu,
    CAST(FLOOR(time / 300000000.0) AS INT64) AS window_index
  FROM `google.com:google-cluster-data.powerdata_2019.cellf_*`
  WHERE NOT bad_measurement_data
    AND NOT bad_production_power_data
    AND CAST(FLOOR(time / 300000000.0) AS INT64) BETWEEN min_window_index AND max_window_index
  GROUP BY 1, 2
),
coverage AS (
  SELECT
    p.pdu,
    COUNT(*) AS power_windows,
    COUNTIF(u.window_index IS NOT NULL) AS matched_usage_windows,
    COUNTIF(u.window_index IS NULL) AS unmatched_usage_windows,
    SAFE_DIVIDE(COUNTIF(u.window_index IS NOT NULL), COUNT(*)) AS matched_ratio
  FROM power_windows AS p
  LEFT JOIN usage_windows AS u
    USING (pdu, window_index)
  GROUP BY 1
)
SELECT
  pdu,
  power_windows,
  matched_usage_windows,
  unmatched_usage_windows,
  matched_ratio,
  CASE
    WHEN matched_ratio >= 0.98 AND matched_usage_windows >= 300 THEN 'strong_dev_candidate'
    WHEN matched_ratio >= 0.95 AND matched_usage_windows >= 200 THEN 'usable_dev_candidate'
    WHEN matched_ratio >= 0.90 AND matched_usage_windows >= 150 THEN 'holdout_or_backup_candidate'
    ELSE 'drop_for_now'
  END AS recommendation
FROM coverage
ORDER BY matched_ratio DESC, matched_usage_windows DESC, pdu;
