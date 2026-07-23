// SpectraCQ RAN4_P3_CQ1-4 (RAN4, phase 3) -- CQ1_TS
// Question: List the level-1 sections of spec 38.133 (top-level structure).
// Gold: 190 rows, primary column "s.sectionId"

MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
