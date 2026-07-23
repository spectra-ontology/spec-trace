// SpectraCQ RAN5_P3_CQ1-9 (RAN5, phase 3) -- CQ1_TS
// Question: Find sections of TS 38.533 whose title contains 'measurement' (topic search).
// Gold: 25 rows, primary column "s.sectionId"

MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}) WHERE toLower(s.sectionTitle) CONTAINS 'measurement' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
