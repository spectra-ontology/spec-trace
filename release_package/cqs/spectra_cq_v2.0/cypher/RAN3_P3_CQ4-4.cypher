// SpectraCQ RAN3_P3_CQ4-4 (RAN3, phase 3) -- CQ4_Resolution
// Question: Return the top 5 specs most modified via the resolution-to-CR-to-spec path (decision-driven change ranking).
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(DISTINCT r) AS resolutions, count(DISTINCT cr) AS crs ORDER BY resolutions DESC LIMIT 5
