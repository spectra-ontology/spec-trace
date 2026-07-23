// SpectraCQ RAN5_P3_CQ1-1 (RAN5, phase 3) -- CQ1_TS
// Question: List the sections of TS 38.533 (structure browsing).
// Gold: 25 rows, primary column "s.sectionId"

MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle, s.level ORDER BY s.sectionNumber LIMIT 25
