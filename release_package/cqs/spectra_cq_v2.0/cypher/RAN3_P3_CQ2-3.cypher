// SpectraCQ RAN3_P3_CQ2-3 (RAN3, phase 3) -- CQ2_TS
// Question: Return the most-referenced sections within spec 38.413 (identifying key sections).
// Gold: 10 rows, primary column "s2.sectionId"

MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.413'}), (s1)-[:REFERENCES_SECTION]->(s2:Section) RETURN s2.sectionId, count(*) AS refs ORDER BY refs DESC, s2.sectionId LIMIT 10
