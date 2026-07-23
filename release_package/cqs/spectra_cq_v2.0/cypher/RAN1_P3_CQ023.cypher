// SpectraCQ RAN1_P3_CQ023 (RAN1, phase 3) -- Resolution_TS
// Question: How many agreements approved CRs modifying TS 38.214? (how active decision-making is here)
// Gold: 1 rows, primary column "agrCount"

MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) RETURN count(DISTINCT agr) AS agrCount
