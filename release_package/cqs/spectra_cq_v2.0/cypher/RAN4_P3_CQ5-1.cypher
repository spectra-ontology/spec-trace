// SpectraCQ RAN4_P3_CQ5-1 (RAN4, phase 3) -- CQ5
// Question: What is the total number of CRs modifying spec 38.133? (overall change volume).
// Gold: 1 rows, primary column "totalCRs"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN count(cr) AS totalCRs
