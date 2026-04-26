-- Purpose: export task-level workload traces with scheduling metadata for flexibility modeling.
-- This script keeps both task usage and scheduler-side lifecycle fields so downstream code can
-- build proxy deadlines, deferrable/critical states, and PDU-window flex summaries.
--
-- Suggested first run:
-- 1) target_cell = 'f'
-- 2) development PDUs: pdu20, pdu21, pdu22, pdu23, pdu24
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
  power_5m AS (
    SELECT
      cell,
      pdu,
      CAST(FLOOR(time / 300000000.0) AS INT64) AS window_index,
      TIMESTAMP_MICROS(CAST(FLOOR(time / 300000000.0) AS INT64) * 300000000) AS window_start,
      AVG(measured_power_util) AS measured_power_util,
      AVG(production_power_util) AS production_power_util
    FROM `google.com:google-cluster-data.powerdata_2019.cell%s_*`
    WHERE _TABLE_SUFFIX IN UNNEST(@target_pdus)
      AND NOT bad_measurement_data
      AND NOT bad_production_power_data
      AND CAST(FLOOR(time / 300000000.0) AS INT64) BETWEEN @min_window_index AND @max_window_index
    GROUP BY 1, 2, 3, 4
  ),
  usage_base AS (
    SELECT
      tm.cell,
      tm.pdu,
      CAST(FLOOR(u.start_time / 300000000.0) AS INT64) AS window_index,
      TIMESTAMP_MICROS(CAST(FLOOR(u.start_time / 300000000.0) AS INT64) * 300000000) AS window_start,
      u.start_time,
      u.end_time,
      u.collection_id,
      u.instance_index,
      u.machine_id,
      u.alloc_collection_id,
      u.alloc_instance_index,
      u.collection_type,
      u.average_usage.cpus AS avg_cpu_usage,
      u.maximum_usage.cpus AS max_cpu_usage,
      u.assigned_memory,
      u.page_cache_memory,
      u.cycles_per_instruction,
      u.memory_accesses_per_instruction,
      u.sample_rate
    FROM `google.com:google-cluster-data.clusterdata_2019_%s.instance_usage` AS u
    JOIN target_machines AS tm
      ON u.machine_id = tm.machine_id
    WHERE CAST(FLOOR(u.start_time / 300000000.0) AS INT64) BETWEEN @min_window_index AND @max_window_index
  ),
  target_collections AS (
    SELECT DISTINCT collection_id
    FROM usage_base
  ),
  collection_lifecycle AS (
    SELECT
      e.collection_id,
      MIN(IF(e.type = 0, e.time, NULL)) AS collection_submit_time,
      MIN(IF(e.type = 3, e.time, NULL)) AS collection_schedule_time,
      MIN(IF(e.type IN (5, 6, 7, 8), e.time, NULL)) AS collection_end_time,
      MAX(CAST(e.scheduling_class AS INT64)) AS collection_scheduling_class,
      MAX(CAST(e.collection_type AS INT64)) AS collection_type_event,
      MAX(e.priority) AS collection_priority,
      MAX(CAST(e.scheduler AS INT64)) AS preferred_scheduler,
      MAX(ARRAY_LENGTH(e.start_after_collection_ids)) AS dependency_count,
      MAX(CAST(e.vertical_scaling AS INT64)) AS vertical_scaling
    FROM `google.com:google-cluster-data.clusterdata_2019_%s.collection_events` AS e
    JOIN target_collections AS tc
      USING (collection_id)
    GROUP BY 1
  ),
  instance_lifecycle AS (
    SELECT
      e.collection_id,
      e.instance_index,
      MIN(IF(e.type = 0, e.time, NULL)) AS instance_submit_time,
      MIN(IF(e.type = 1, e.time, NULL)) AS instance_queue_time,
      MIN(IF(e.type = 2, e.time, NULL)) AS instance_enable_time,
      MIN(IF(e.type = 3, e.time, NULL)) AS instance_start_time,
      MIN(IF(e.type IN (4, 5, 6, 7, 8), e.time, NULL)) AS instance_end_time,
      MAX(CAST(e.scheduling_class AS INT64)) AS instance_scheduling_class,
      MAX(e.priority) AS instance_priority
    FROM `google.com:google-cluster-data.clusterdata_2019_%s.instance_events` AS e
    JOIN target_collections AS tc
      USING (collection_id)
    GROUP BY 1, 2
  )
  SELECT
    u.window_start,
    u.window_index,
    u.cell,
    u.pdu,
    u.start_time,
    u.end_time,
    u.collection_id,
    u.instance_index,
    u.machine_id,
    u.alloc_collection_id,
    u.alloc_instance_index,
    CAST(COALESCE(u.collection_type, c.collection_type_event) AS INT64) AS collection_type,
    c.collection_submit_time,
    c.collection_schedule_time,
    c.collection_end_time,
    c.collection_scheduling_class,
    c.collection_priority,
    c.preferred_scheduler,
    c.dependency_count,
    c.vertical_scaling,
    i.instance_submit_time,
    i.instance_queue_time,
    i.instance_enable_time,
    i.instance_start_time,
    i.instance_end_time,
    i.instance_scheduling_class,
    i.instance_priority,
    u.avg_cpu_usage,
    u.max_cpu_usage,
    u.assigned_memory,
    u.page_cache_memory,
    u.cycles_per_instruction,
    u.memory_accesses_per_instruction,
    u.sample_rate,
    p.measured_power_util,
    p.production_power_util
  FROM usage_base AS u
  LEFT JOIN collection_lifecycle AS c
    USING (collection_id)
  LEFT JOIN instance_lifecycle AS i
    USING (collection_id, instance_index)
  LEFT JOIN power_5m AS p
    USING (cell, pdu, window_index, window_start)
  ORDER BY u.cell, u.pdu, u.window_start, u.collection_id, u.instance_index
""", target_cell, target_cell, target_cell, target_cell)
USING
  target_cell AS target_cell,
  target_pdus AS target_pdus,
  min_window_index AS min_window_index,
  max_window_index AS max_window_index;
