// SpectraCQ RAN3_P3_CQ4-1 (RAN3, phase 3) -- CQ4_Resolution
// Question: Return the specs modified by CRs that resolutions approved (decision-to-spec impact).
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(r) AS resolutions ORDER BY resolutions DESC LIMIT 10
