// SpectraCQ RAN4_P3_CQ2-4 (RAN4, phase 3) -- CQ2_TS
// Question: List the top 10 sections that reference the most others (heaviest referencing clauses).
// Gold: 10 rows, primary column "a.sectionId"

MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH a, count(b) AS outCount RETURN a.sectionId, outCount ORDER BY outCount DESC, a.sectionId LIMIT 10
