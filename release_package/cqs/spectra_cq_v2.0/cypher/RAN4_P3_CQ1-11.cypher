// SpectraCQ RAN4_P3_CQ1-11 (RAN4, phase 3) -- CQ1_TS
// Question: List the level-2 sections of spec 38.104 (base-station spec structure).
// Gold: 25 rows, primary column "s.sectionId"

MATCH (s:Section {level: 2})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.104'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber LIMIT 25
