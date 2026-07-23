// SpectraCQ RAN5_P3_CQ2-3 (RAN5, phase 3) -- CQ2_TS
// Question: Which ten sections make the most outgoing references? (heaviest referrers)
// Gold: 10 rows, primary column "a.sectionId"

MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH a, count(b) AS outCount RETURN a.sectionId, outCount ORDER BY outCount DESC, a.sectionId LIMIT 10
