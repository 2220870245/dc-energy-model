-- Purpose: export aggregated flexibility windows directly from BigQuery.
-- This avoids the very large task-level csv volume of 08_export_task_flexibility_trace.sql
-- by deriving proxy task states inside BigQuery and only returning PDU x 5-minute summaries.
--
-- Suggested first run:
-- 1) target_cell = 'f'
-- 2) development PDUs: pdu20, pdu21, pdu22, pdu23, pdu24
-- 3) time range: window_index 1500-2100
-- 4) rho = 1.5

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
DECLARE rho FLOAT64 DEFAULT 1.5;
DECLARE max_flex_scheduling_class INT64 DEFAULT 1;
DECLARE require_batch_scheduler BOOL DEFAULT TRUE;

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
      u.collection_type,
      u.average_usage.cpus AS avg_cpu_usage,
      u.maximum_usage.cpus AS max_cpu_usage
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
      MAX(ARRAY_LENGTH(e.start_after_collection_ids)) AS dependency_count
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
  ),
  task_states AS (
    SELECT
      u.window_start,
      u.window_index,
      u.cell,
      u.pdu,
      u.collection_id,
      u.instance_index,
      u.machine_id,
      u.avg_cpu_usage,
      u.max_cpu_usage,
      COALESCE(i.instance_scheduling_class, c.collection_scheduling_class, 99) AS effective_scheduling_class,
      COALESCE(i.instance_priority, c.collection_priority, 0) AS effective_priority,
      COALESCE(c.preferred_scheduler, 0) AS effective_scheduler,
      COALESCE(c.dependency_count, 0) AS dependency_count,
      COALESCE(u.collection_type, c.collection_type_event, 0) AS effective_collection_type,
      COALESCE(i.instance_submit_time, c.collection_submit_time, u.start_time) AS submit_time_us,
      COALESCE(i.instance_start_time, c.collection_schedule_time, u.start_time) AS run_start_time_us,
      COALESCE(i.instance_end_time, c.collection_end_time, u.end_time) AS run_end_time_us,
      u.end_time
    FROM usage_base AS u
    LEFT JOIN collection_lifecycle AS c
      USING (collection_id)
    LEFT JOIN instance_lifecycle AS i
      USING (collection_id, instance_index)
  ),
  classified_tasks AS (
    SELECT
      window_start,
      window_index,
      cell,
      pdu,
      collection_id,
      instance_index,
      machine_id,
      avg_cpu_usage,
      max_cpu_usage,
      effective_scheduling_class,
      effective_priority,
      effective_scheduler,
      dependency_count,
      GREATEST(run_end_time_us - run_start_time_us, 300000000) AS actual_runtime_us,
      submit_time_us + @rho * GREATEST(run_end_time_us - run_start_time_us, 300000000) AS proxy_deadline_us,
      (
        submit_time_us + @rho * GREATEST(run_end_time_us - run_start_time_us, 300000000)
      ) - (
        end_time + GREATEST(run_end_time_us - run_start_time_us, 300000000)
      ) AS remaining_slack_us,
      effective_collection_type = 0 AS is_job,
      effective_scheduling_class <= @max_flex_scheduling_class AS scheduling_class_flexible,
      effective_scheduler = 1 AS is_batch_scheduler
    FROM task_states
  ),
  final_tasks AS (
    SELECT
      *,
      is_job
        AND scheduling_class_flexible
        AND (NOT @require_batch_scheduler OR is_batch_scheduler) AS is_flex_candidate,
      is_job
        AND scheduling_class_flexible
        AND (NOT @require_batch_scheduler OR is_batch_scheduler)
        AND remaining_slack_us <= 0 AS is_critical
    FROM classified_tasks
  )
  SELECT
    t.window_start,
    t.window_index,
    t.cell,
    t.pdu,
    COUNT(*) AS task_count,
    COUNT(DISTINCT t.collection_id) AS job_count,
    COUNT(DISTINCT t.machine_id) AS machine_count,
    SUM(t.avg_cpu_usage) AS total_cpu_usage,
    SUM(IF(NOT t.is_flex_candidate, t.avg_cpu_usage, 0.0)) AS online_cpu_usage,
    SUM(IF(t.is_flex_candidate AND NOT t.is_critical, t.avg_cpu_usage, 0.0)) AS flex_cpu_usage,
    SUM(IF(t.is_critical, t.avg_cpu_usage, 0.0)) AS critical_cpu_usage,
    SUM(IF(t.is_flex_candidate, t.avg_cpu_usage, 0.0)) AS batch_candidate_cpu_usage,
    COUNTIF(NOT t.is_flex_candidate) AS online_task_count,
    COUNTIF(t.is_flex_candidate AND NOT t.is_critical) AS deferrable_task_count,
    COUNTIF(t.is_critical) AS critical_task_count,
    AVG(IF(t.is_flex_candidate AND NOT t.is_critical, t.remaining_slack_us, NULL)) AS mean_deferrable_slack_us,
    MAX(t.dependency_count) AS max_dependency_count,
    AVG(t.effective_priority) AS mean_priority,
    AVG(CAST(t.effective_scheduling_class AS FLOAT64)) AS mean_scheduling_class,
    IF(SUM(t.avg_cpu_usage) > 0, SUM(IF(t.is_flex_candidate AND NOT t.is_critical, t.avg_cpu_usage, 0.0)) / SUM(t.avg_cpu_usage), 0.0) AS flex_cpu_ratio,
    IF(SUM(t.avg_cpu_usage) > 0, SUM(IF(t.is_critical, t.avg_cpu_usage, 0.0)) / SUM(t.avg_cpu_usage), 0.0) AS critical_cpu_ratio,
    IF(SUM(t.avg_cpu_usage) > 0, SUM(IF(NOT t.is_flex_candidate, t.avg_cpu_usage, 0.0)) / SUM(t.avg_cpu_usage), 0.0) AS online_cpu_ratio,
    p.measured_power_util,
    p.production_power_util
  FROM final_tasks AS t
  LEFT JOIN power_5m AS p
    USING (cell, pdu, window_index, window_start)
  GROUP BY 1, 2, 3, 4, p.measured_power_util, p.production_power_util
  ORDER BY window_start, cell, pdu
""", target_cell, target_cell, target_cell, target_cell)
USING
  target_cell AS target_cell,
  target_pdus AS target_pdus,
  min_window_index AS min_window_index,
  max_window_index AS max_window_index,
  rho AS rho,
  max_flex_scheduling_class AS max_flex_scheduling_class,
  require_batch_scheduler AS require_batch_scheduler;
