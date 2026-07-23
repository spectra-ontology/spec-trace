// SpectraCQ RAN5_P3_CQ5-1 (RAN5, phase 3) -- CQ5
// Question: List all CRs changing TS 38.521-1 (comprehensive change survey).
// Gold: 10 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.521-1'}) RETURN cr.tdocNumber, cr.title ORDER BY cr.tdocNumber DESC LIMIT 10
