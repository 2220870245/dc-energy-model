-- Purpose: validate how many power windows have a matching usage aggregate.

DECLARE cell STRING DEFAULT 'f';
DECLARE pdu_num STRING DEFAULT '17';

EXECUTE IMMEDIATE FORMAT("""
  WITH target_machines AS (
    SELECT machine_id
    FROM `google.com:google-cluster-data.powerdata_2019.machine_to_pdu_mapping`
    WHERE pdu = 'pdu%s'
  ),
  power_trace AS (
    SELECT time AS window_start
    FROM `google.com:google-cluster-data.powerdata_2019.cell%s_pdu%s`
  ),
  usage_windows AS (
    SELECT DISTINCT u.start_time AS window_start
    FROM `google.com:google-cluster-data.clusterdata_2019_%s.instance_usage` AS u
    JOIN target_machines AS tm
      ON u.machine_id = tm.machine_id
    WHERE (u.alloc_collection_id IS NULL OR u.alloc_collection_id = 0)
      AND (u.end_time - u.start_time) >= (5 * 60 * 1000000)
  )
  SELECT
    COUNT(*) AS total_power_windows,
    COUNTIF(u.window_start IS NOT NULL) AS matched_windows,
    COUNTIF(u.window_start IS NULL) AS unmatched_windows,
    SAFE_DIVIDE(COUNTIF(u.window_start IS NOT NULL), COUNT(*)) AS matched_ratio
  FROM power_trace AS p
  LEFT JOIN usage_windows AS u
    USING (window_start)
""", pdu_num, cell, pdu_num, cell);
