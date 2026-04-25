-- Purpose: join instance usage with the machines inside one PDU.
-- This query keeps only a minimum feature set for the first validation pass.

DECLARE cell STRING DEFAULT 'f';
DECLARE pdu_num STRING DEFAULT '17';

EXECUTE IMMEDIATE FORMAT("""
  WITH target_machines AS (
    SELECT machine_id
    FROM `google.com:google-cluster-data.powerdata_2019.machine_to_pdu_mapping`
    WHERE pdu = 'pdu%s'
  )
  SELECT
    u.start_time AS window_start,
    u.end_time AS window_end,
    u.collection_id,
    u.instance_index,
    u.machine_id,
    u.average_usage.cpus AS cpu_usage,
    e.priority AS priority
  FROM `google.com:google-cluster-data.clusterdata_2019_%s.instance_usage` AS u
  LEFT JOIN (
    SELECT
      collection_id,
      instance_index,
      machine_id,
      MAX(priority) AS priority
    FROM `google.com:google-cluster-data.clusterdata_2019_%s.instance_events`
    WHERE (alloc_collection_id IS NULL OR alloc_collection_id = 0)
    GROUP BY 1, 2, 3
  ) AS e
    ON u.collection_id = e.collection_id
   AND u.instance_index = e.instance_index
   AND u.machine_id = e.machine_id
  JOIN target_machines AS tm
    ON u.machine_id = tm.machine_id
  WHERE (u.alloc_collection_id IS NULL OR u.alloc_collection_id = 0)
    AND (u.end_time - u.start_time) >= (5 * 60 * 1000000)
  ORDER BY window_start, machine_id, collection_id, instance_index
""", pdu_num, cell, cell);
