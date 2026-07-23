// SpectraCQ RAN5_P3_CQ2-2 (RAN5, phase 3) -- CQ2_TS
// Question: Which ten sections are referenced most often? (most-cited clauses)
// Gold: 10 rows, primary column "b.sectionId"

MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH b, count(a) AS refCount RETURN b.sectionId, b.sectionTitle, refCount ORDER BY refCount DESC LIMIT 10
