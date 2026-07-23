// SpectraCQ RAN1_P1_CQ2-4 (RAN1, phase 1) -- CQ2_Tdoc
// Question: List the CRs modifying TS 38.214 with their status (revision status of 38.214).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.214'}) WHERE t.type IN ['CR', 'draftCR'] RETURN t.tdocNumber, t.title, t.status, t.type ORDER BY t.tdocNumber ASC LIMIT 1
