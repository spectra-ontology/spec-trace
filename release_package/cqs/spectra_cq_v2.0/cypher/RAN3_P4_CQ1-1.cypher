// SpectraCQ RAN3_P4_CQ1-1 (RAN3, phase 4) -- CQ1
// Question: Return the reason-for-change of CR R3-237113 (change-rationale review).
// Gold: 1 rows, primary column "reasonForChange"

MATCH (c:CR {tdocNumber: 'R3-237113'}) RETURN c.reasonForChange AS reasonForChange LIMIT 1
