-- Purpose: build the first 5-minute PDU training base with CPU aggregation and power labels.
-- This intentionally starts with CPU-based features before adding more fields.

DECLARE cell STRING DEFAULT 'f';
DECLARE pdu_num STRING DEFAULT '17';

EXECUTE IMMEDIATE FORMAT("""
  WITH target_machines AS (
    SELECT machine_id
    FROM `google.com:google-cluster-data.powerdata_2019.machine_to_pdu_mapping`
    WHERE pdu = 'pdu%s'
  ),
  power_trace AS (
    SELECT
      time AS window_start,
      cell,
      pdu,
      measured_power_util,
      production_power_util
    FROM `google.com:google-cluster-data.powerdata_2019.cell%s_pdu%s`
  ),
  usage_base AS (
    SELECT
      u.start_time AS window_start,
      u.machine_id,
      u.collection_id,
      u.instance_index,
      u.average_usage.cpus AS cpu_usage
    FROM `google.com:google-cluster-data.clusterdata_2019_%s.instance_usage` AS u
    JOIN target_machines AS tm
      ON u.machine_id = tm.machine_id
    WHERE (u.alloc_collection_id IS NULL OR u.alloc_collection_id = 0)
      AND (u.end_time - u.start_time) >= (5 * 60 * 1000000)
  ),
  usage_agg AS (
    SELECT
      window_start,
      COUNT(*) AS instance_count,
      COUNT(DISTINCT collection_id) AS collection_count,
      COUNT(DISTINCT machine_id) AS machine_count,
      SUM(cpu_usage) AS total_cpu_usage,
      AVG(cpu_usage) AS avg_cpu_usage,
      MAX(cpu_usage) AS max_cpu_usage
    FROM usage_base
    GROUP BY 1
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
  FROM power_trace AS p
  LEFT JOIN usage_agg AS u
    USING (window_start)
  ORDER BY p.window_start
""", pdu_num, cell, pdu_num, cell);
