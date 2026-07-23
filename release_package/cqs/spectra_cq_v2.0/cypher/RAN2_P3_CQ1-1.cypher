// SpectraCQ RAN2_P3_CQ1-1 (RAN2, phase 3) -- CQ1_TS
// Question: List all sections of spec 38.331 (RRC structure overview).
// Gold: 25 rows, primary column "s.sectionId"

MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle, s.level ORDER BY s.sectionNumber LIMIT 25
