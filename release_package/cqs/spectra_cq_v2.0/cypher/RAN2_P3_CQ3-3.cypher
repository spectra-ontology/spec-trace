// SpectraCQ RAN2_P3_CQ3-3 (RAN2, phase 3) -- CQ3_CR
// Question: List the CRs that modify spec 38.331 (change history).
// Gold: 10 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}) RETURN cr.tdocNumber, cr.title, cr.status ORDER BY cr.tdocNumber DESC LIMIT 10
