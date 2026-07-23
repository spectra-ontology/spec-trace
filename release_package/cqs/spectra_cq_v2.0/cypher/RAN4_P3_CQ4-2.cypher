// SpectraCQ RAN4_P3_CQ4-2 (RAN4, phase 3) -- CQ4_Resolution
// Question: How many resolutions approved CRs that modify spec 38.133? (decision volume for a spec).
// Gold: 1 rows, primary column "resolutionCount"

MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN count(DISTINCT r) AS resolutionCount
