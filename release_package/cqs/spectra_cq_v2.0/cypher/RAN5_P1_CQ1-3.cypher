// SpectraCQ RAN5_P1_CQ1-3 (RAN5, phase 1) -- 
// Question: Show the details of a CR (R5-255xxx) and the spec it modifies (change-request lookup).
// Gold: 5 rows, primary column "cr.tdocNumber"

MATCH (cr:CR) WHERE cr.tdocNumber STARTS WITH 'R5-255' OPTIONAL MATCH (cr)-[:MODIFIES]->(sp:Spec) RETURN cr.tdocNumber, cr.title, sp.specNumber ORDER BY cr.tdocNumber, sp.specNumber LIMIT 5
