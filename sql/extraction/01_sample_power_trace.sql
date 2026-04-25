-- Purpose: fetch a small sample from one power domain.
-- Based on the official Google power trace analysis notebook.

DECLARE cell STRING DEFAULT 'f';
DECLARE pdu_num STRING DEFAULT '17';
DECLARE row_limit INT64 DEFAULT 288;

EXECUTE IMMEDIATE FORMAT("""
  SELECT
    time,
    cell,
    pdu,
    measured_power_util,
    production_power_util
  FROM `google.com:google-cluster-data.powerdata_2019.cell%s_pdu%s`
  ORDER BY time
  LIMIT %d
""", cell, pdu_num, row_limit);
