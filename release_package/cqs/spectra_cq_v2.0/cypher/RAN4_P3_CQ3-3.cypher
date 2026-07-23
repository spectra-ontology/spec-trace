// SpectraCQ RAN4_P3_CQ3-3 (RAN4, phase 3) -- CQ3_CR
// Question: List the top 10 CRs that modify spec 38.133 (recent changes to the spec).
// Gold: 10 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN cr.tdocNumber, cr.title ORDER BY cr.tdocNumber DESC LIMIT 10
