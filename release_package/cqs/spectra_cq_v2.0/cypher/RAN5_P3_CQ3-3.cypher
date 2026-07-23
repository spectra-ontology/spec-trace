// SpectraCQ RAN5_P3_CQ3-3 (RAN5, phase 3) -- CQ3_CR
// Question: List the CRs that modify TS 38.521-1 (change-request survey).
// Gold: 10 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.521-1'}) RETURN cr.tdocNumber, cr.title ORDER BY cr.tdocNumber DESC LIMIT 10
