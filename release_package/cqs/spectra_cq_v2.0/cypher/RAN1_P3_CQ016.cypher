// SpectraCQ RAN1_P3_CQ016 (RAN1, phase 3) -- CR_TS
// Question: How many CRs have been raised against TS 38.214? (how actively it is revised)
// Gold: 1 rows, primary column "totalCR"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) RETURN count(cr) AS totalCR
