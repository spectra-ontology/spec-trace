// SpectraCQ RAN4_P3_CQ1-13 (RAN4, phase 3) -- CQ1_TS
// Question: List the void sections of spec 38.133 (identifying deprecated clauses).
// Gold: 25 rows, primary column "s.sectionId"

MATCH (s:Section {isVoid: true})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
