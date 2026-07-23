// SpectraCQ RAN3_P3_CQ3-3 (RAN3, phase 3) -- CQ3_CR
// Question: List the CRs that modify spec 38.423 (change history of a spec).
// Gold: 10 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.423'}) RETURN cr.tdocNumber, cr.title, cr.status ORDER BY cr.tdocNumber DESC LIMIT 10
