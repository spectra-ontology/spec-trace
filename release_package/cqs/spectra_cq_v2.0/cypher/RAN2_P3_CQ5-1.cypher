// SpectraCQ RAN2_P3_CQ5-1 (RAN2, phase 3) -- CQ5
// Question: Return the total number of CRs modifying spec 38.331 (change volume).
// Gold: 1 rows, primary column "totalCRs"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}) RETURN count(cr) AS totalCRs
