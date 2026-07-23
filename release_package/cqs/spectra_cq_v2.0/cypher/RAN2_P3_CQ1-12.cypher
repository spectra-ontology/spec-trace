// SpectraCQ RAN2_P3_CQ1-12 (RAN2, phase 3) -- CQ1_TS
// Question: Return the section-level distribution of spec 38.331 (structural depth profile).
// Gold: 7 rows, primary column "s.level"

MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN s.level, count(s) AS cnt ORDER BY s.level
