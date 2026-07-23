// SpectraCQ RAN4_P1_CQ2-2 (RAN4, phase 1) -- 
// Question: List the CRs that modify spec 38.101-1 (spec change tracking).
// Gold: 10 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber:'38.101-1'}) RETURN cr.tdocNumber ORDER BY cr.tdocNumber DESC LIMIT 10
