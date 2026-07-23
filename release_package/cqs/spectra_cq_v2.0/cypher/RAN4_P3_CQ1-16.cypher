// SpectraCQ RAN4_P3_CQ1-16 (RAN4, phase 3) -- CQ1_TS
// Question: List the top 5 RAN4 specs by section count (largest specs).
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(s) AS sectionCount ORDER BY sectionCount DESC LIMIT 5
