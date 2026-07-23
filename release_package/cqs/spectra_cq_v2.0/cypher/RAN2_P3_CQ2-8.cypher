// SpectraCQ RAN2_P3_CQ2-8 (RAN2, phase 3) -- CQ2_TS
// Question: Return the top 5 most-referenced sections within spec 38.331 (internal hubs).
// Gold: 5 rows, primary column "s2.sectionId"

MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN s2.sectionId, s2.sectionTitle, count(*) AS refCount ORDER BY refCount DESC, s2.sectionId LIMIT 5
