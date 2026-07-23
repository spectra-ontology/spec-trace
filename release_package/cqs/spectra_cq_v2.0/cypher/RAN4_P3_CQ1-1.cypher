// SpectraCQ RAN4_P3_CQ1-1 (RAN4, phase 3) -- CQ1_TS
// Question: List the sections of spec 38.133 (spec structure browsing).
// Gold: 25 rows, primary column "s.sectionId"

MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle, s.level ORDER BY s.sectionNumber LIMIT 25
