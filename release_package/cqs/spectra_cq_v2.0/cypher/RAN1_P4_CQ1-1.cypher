// SpectraCQ RAN1_P4_CQ1-1 (RAN1, phase 4) -- CQ1_CR
// Question: What is the specific reason-for-change of CR R1-2504971, which touches five specs to introduce LP-WUS/WUR? (rationale review)
// Gold: 1 rows, primary column "cr.tdocNumber"

MATCH (cr:CR {tdocNumber: 'R1-2504971'}) WHERE cr.reasonForChange IS NOT NULL RETURN cr.tdocNumber, cr.reasonForChange
