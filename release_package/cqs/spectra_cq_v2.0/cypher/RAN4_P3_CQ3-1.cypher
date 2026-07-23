// SpectraCQ RAN4_P3_CQ3-1 (RAN4, phase 3) -- CQ3_CR
// Question: Which specs does CR RP-240001 modify? (change-request impact lookup).
// Gold: 1 rows, primary column "cr2.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WITH cr, sp ORDER BY cr.tdocNumber, sp.specNumber LIMIT 1 MATCH (cr2:CR {tdocNumber: cr.tdocNumber})-[:MODIFIES]->(sp2:Spec) RETURN cr2.tdocNumber, sp2.specNumber ORDER BY cr2.tdocNumber, sp2.specNumber LIMIT 5
