// SpectraCQ RAN2_P3_CQ4-1 (RAN2, phase 3) -- CQ4_Resolution
// Question: Which specs are modified by CRs approved via resolutions (decision-to-spec trace)?
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(r) AS resolutions ORDER BY resolutions DESC LIMIT 10
