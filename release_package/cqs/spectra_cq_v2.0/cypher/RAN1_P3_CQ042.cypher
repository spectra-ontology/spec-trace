// SpectraCQ RAN1_P3_CQ042 (RAN1, phase 3) -- 
// Question: Which are the top 10 areas rich in both sections and tables? (high implementation difficulty)
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (sec:Section)-[:CONTAINS_TABLE]->(tbl:TSTable) WITH sec, count(tbl) AS tableCount WHERE tableCount >= 3 MATCH (sec)-[:BELONGS_TO_SPEC]->(sp:Spec) OPTIONAL MATCH (sec)-[:HAS_SUB_SECTION]->(sub:Section) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, tableCount, count(sub) AS subSectionCount ORDER BY tableCount DESC LIMIT 10
