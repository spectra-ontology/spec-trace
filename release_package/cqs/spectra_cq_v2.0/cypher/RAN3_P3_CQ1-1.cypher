// SpectraCQ RAN3_P3_CQ1-1 (RAN3, phase 3) -- CQ1_TS
// Question: List all sections of spec 38.423 (full-structure overview).
// Gold: 25 rows, primary column "s.sectionId"

MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle, s.level ORDER BY s.sectionNumber LIMIT 25
