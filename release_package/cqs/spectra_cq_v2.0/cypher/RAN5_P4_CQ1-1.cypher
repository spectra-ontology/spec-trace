// SpectraCQ RAN5_P4_CQ1-1 (RAN5, phase 4) -- CQ1
// Question: Give the reason-for-change of CR R5-261671 (change rationale).
// Gold: 1 rows, primary column "reasonForChange"

MATCH (c:CR {tdocNumber: 'R5-261671'}) RETURN c.reasonForChange AS reasonForChange LIMIT 1
