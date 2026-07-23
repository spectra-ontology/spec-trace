// SpectraCQ RAN3_P3_CQ1-11 (RAN3, phase 3) -- CQ1_TS
// Question: Return the top 5 specs by section count (largest specs by structure).
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(s) AS sectionCount ORDER BY sectionCount DESC LIMIT 5
