// SpectraCQ RAN4_P3_CQ1-9 (RAN4, phase 3) -- CQ1_TS
// Question: List the sections of spec 38.133 whose title contains 'measurement' (finding measurement clauses).
// Gold: 25 rows, primary column "s.sectionId"

MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) WHERE toLower(s.sectionTitle) CONTAINS 'measurement' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionNumber LIMIT 25
