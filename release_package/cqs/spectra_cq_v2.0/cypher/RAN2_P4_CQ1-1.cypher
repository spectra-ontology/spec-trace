// SpectraCQ RAN2_P4_CQ1-1 (RAN2, phase 4) -- CQ1
// Question: Return the reason for change of CR R2-2508534 (change rationale).
// Gold: 1 rows, primary column "reasonForChange"

MATCH (c:CR {tdocNumber: 'R2-2508534'}) RETURN c.reasonForChange AS reasonForChange LIMIT 1
