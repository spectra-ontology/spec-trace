// SpectraCQ RAN3_P3_CQ1-15 (RAN3, phase 3) -- CQ1_TS
// Question: Return the top 5 sections by table count (table-dense sections).
// Gold: 5 rows, primary column "s.sectionId"

MATCH (s:Section)-[:CONTAINS_TABLE]->(t:TSTable) RETURN s.sectionId, count(t) AS tableCount ORDER BY tableCount DESC, s.sectionId LIMIT 5
