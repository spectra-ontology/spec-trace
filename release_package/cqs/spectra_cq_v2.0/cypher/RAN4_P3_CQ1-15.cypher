// SpectraCQ RAN4_P3_CQ1-15 (RAN4, phase 3) -- CQ1_TS
// Question: List the level-3 sections of spec 38.133 (deep-structure browsing).
// Gold: 25 rows, primary column "s.sectionId"

MATCH (s:Section {level: 3})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
