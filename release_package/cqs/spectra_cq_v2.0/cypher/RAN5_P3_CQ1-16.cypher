// SpectraCQ RAN5_P3_CQ1-16 (RAN5, phase 3) -- CQ1_TS
// Question: Which five RAN5 specs have the most sections? (largest specs)
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN sp.specNumber, count(s) AS sectionCount ORDER BY sectionCount DESC LIMIT 5
