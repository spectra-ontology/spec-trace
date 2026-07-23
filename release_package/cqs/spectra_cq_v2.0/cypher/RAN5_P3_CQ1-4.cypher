// SpectraCQ RAN5_P3_CQ1-4 (RAN5, phase 3) -- CQ1_TS
// Question: List the level-1 sections of TS 38.533 (top-level outline).
// Gold: 231 rows, primary column "s.sectionId"

MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
