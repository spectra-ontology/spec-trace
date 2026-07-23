// SpectraCQ RAN4_P3_CQ2-3 (RAN4, phase 3) -- CQ2_TS
// Question: List the top 10 most-referenced sections (key referenced clauses).
// Gold: 10 rows, primary column "b.sectionId"

MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH b, count(a) AS refCount RETURN b.sectionId, b.sectionTitle, refCount ORDER BY refCount DESC, b.sectionId LIMIT 10
