// SpectraCQ RAN5_P1_CQ2-2 (RAN5, phase 1) -- 
// Question: List the CRs that modify TS 38.533 (spec-change tracking).
// Gold: 10 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber:'38.533'}) RETURN cr.tdocNumber ORDER BY cr.tdocNumber DESC LIMIT 10
