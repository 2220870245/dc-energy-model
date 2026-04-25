-- Purpose: list all machines that belong to one target PDU.

DECLARE pdu_num STRING DEFAULT '17';

SELECT
  machine_id,
  pdu
FROM `google.com:google-cluster-data.powerdata_2019.machine_to_pdu_mapping`
WHERE pdu = FORMAT('pdu%s', pdu_num)
ORDER BY machine_id;
