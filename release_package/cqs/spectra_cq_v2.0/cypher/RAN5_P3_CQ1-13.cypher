// SpectraCQ RAN5_P3_CQ1-13 (RAN5, phase 3) -- CQ1_TS
// Question: List the void sections of TS 38.521-1 (identifying removed clauses).
// Gold: 25 rows, primary column "s.sectionId"

MATCH (s:Section {isVoid: true})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-1'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber LIMIT 25
