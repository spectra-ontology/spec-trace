// SpectraCQ RAN5_P3_CQ3-1 (RAN5, phase 3) -- CQ3_CR
// Question: Which RAN5 specs do recent CRs modify? (change-to-spec mapping)
// Gold: 5 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN cr.tdocNumber, sp.specNumber ORDER BY cr.tdocNumber DESC LIMIT 5
