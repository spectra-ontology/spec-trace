// SpectraCQ RAN3_P3_CQ1-12 (RAN3, phase 3) -- CQ1_TS
// Question: Show the section-level distribution in spec 38.423 (structural-depth profile).
// Gold: 4 rows, primary column "s.level"

MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN s.level, count(s) AS cnt ORDER BY s.level
