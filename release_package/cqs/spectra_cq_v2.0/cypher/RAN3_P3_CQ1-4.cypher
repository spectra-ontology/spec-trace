// SpectraCQ RAN3_P3_CQ1-4 (RAN3, phase 3) -- CQ1_TS
// Question: List the level-1 sections of spec 38.413 (top-level table of contents).
// Gold: 55 rows, primary column "s.sectionId"

MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.413'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
