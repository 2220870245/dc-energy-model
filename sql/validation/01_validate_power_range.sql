-- Purpose: validate the power-label range and timestamp continuity for one PDU.

DECLARE cell STRING DEFAULT 'f';
DECLARE pdu_num STRING DEFAULT '17';

EXECUTE IMMEDIATE FORMAT("""
  SELECT
    COUNT(*) AS row_count,
    MIN(time) AS min_time,
    MAX(time) AS max_time,
    MIN(measured_power_util) AS min_measured_power_util,
    MAX(measured_power_util) AS max_measured_power_util,
    MIN(production_power_util) AS min_production_power_util,
    MAX(production_power_util) AS max_production_power_util
  FROM `google.com:google-cluster-data.powerdata_2019.cell%s_pdu%s`
""", cell, pdu_num);
