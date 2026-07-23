// SpectraCQ RAN4_P4_CQ1-1 (RAN4, phase 4) -- CQ1
// Question: Return the reason-for-change of CR R4-2107689 (change rationale review).
// Gold: 1 rows, primary column "reasonForChange"

MATCH (c:CR {tdocNumber: 'R4-2107689'}) RETURN c.reasonForChange AS reasonForChange LIMIT 1
