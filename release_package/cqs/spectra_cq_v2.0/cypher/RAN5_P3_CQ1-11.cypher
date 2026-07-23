// SpectraCQ RAN5_P3_CQ1-11 (RAN5, phase 3) -- CQ1_TS
// Question: List the level-2 sections of TS 38.521-2 (second-level outline).
// Gold: 25 rows, primary column "s.sectionId"

MATCH (s:Section {level: 2})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-2'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
