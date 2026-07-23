// SpectraCQ RAN2_P3_CQ1-4 (RAN2, phase 3) -- CQ1_TS
// Question: List the level-1 sections of spec 38.321 (top-level MAC outline).
// Gold: 40 rows, primary column "s.sectionId"

MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.321'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
