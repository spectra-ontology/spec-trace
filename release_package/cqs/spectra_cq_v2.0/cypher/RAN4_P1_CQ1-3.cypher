// SpectraCQ RAN4_P1_CQ1-3 (RAN4, phase 1) -- 
// Question: Return the details of CR R4-2419229 and the spec it modifies (change-request lookup).
// Gold: 1 rows, primary column "cr.tdocNumber"

MATCH (cr:CR {tdocNumber:'R4-2419229'}) OPTIONAL MATCH (cr)-[:MODIFIES]->(sp:Spec) RETURN cr.tdocNumber, cr.title, sp.specNumber
