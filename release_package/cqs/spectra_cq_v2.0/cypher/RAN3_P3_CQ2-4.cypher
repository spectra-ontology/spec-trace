// SpectraCQ RAN3_P3_CQ2-4 (RAN3, phase 3) -- CQ2_TS
// Question: Return the top 10 most-referenced sections overall (globally cited sections).
// Gold: 10 rows, primary column "s.sectionId"

MATCH (ref:Section)-[:REFERENCES_SECTION]->(s:Section) RETURN s.sectionId, s.sectionTitle, count(ref) AS refCount ORDER BY refCount DESC, s.sectionId LIMIT 10
