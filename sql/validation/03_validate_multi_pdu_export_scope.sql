-- Purpose: validate per-PDU coverage before exporting a multi-PDU training table.
-- Use this first to confirm that each target PDU has power windows and matched usage windows.

DECLARE target_cell STRING DEFAULT 'f';
DECLARE target_pdus ARRAY<STRING> DEFAULT ['pdu17', 'pdu18', 'pdu19'];
DECLARE min_window_index INT64 DEFAULT 1570;
DECLARE max_window_index INT64 DEFAULT 1857;

EXECUTE IMMEDIATE FORMAT("""
  WITH target_machines AS (
    SELECT
      machine_id,
      pdu,
      cell
    FROM `google.com:google-cluster-data.powerdata_2019.machine_to_pdu_mapping`
    WHERE cell = @target_cell
      AND pdu IN UNNEST(@target_pdus)
  ),
  usage_windows AS (
    SELECT
      tm.pdu,
      CAST(FLOOR(u.start_time / 300000000.0) AS INT64) AS window_index
    FROM `google.com:google-cluster-data.clusterdata_2019_%s.instance_usage` AS u
    JOIN target_machines AS tm
      ON u.machine_id = tm.machine_id
    WHERE CAST(FLOOR(u.start_time / 300000000.0) AS INT64) BETWEEN @min_window_index AND @max_window_index
    GROUP BY 1, 2
  ),
  power_windows AS (
    SELECT
      pdu,
      CAST(FLOOR(time / 300000000.0) AS INT64) AS window_index
    FROM `google.com:google-cluster-data.powerdata_2019.cell%s_*`
    WHERE _TABLE_SUFFIX IN UNNEST(@target_pdus)
      AND NOT bad_measurement_data
      AND NOT bad_production_power_data
      AND CAST(FLOOR(time / 300000000.0) AS INT64) BETWEEN @min_window_index AND @max_window_index
    GROUP BY 1, 2
  )
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
  ORDER BY 1
""", target_cell, target_cell)
USING
  target_cell AS target_cell,
  target_pdus AS target_pdus,
  min_window_index AS min_window_index,
  max_window_index AS max_window_index;
