// SpectraCQ RAN1_P3_CQ041 (RAN1, phase 3) -- 
// Question: Which sections contain five or more tables? (parameter-dense implementation points)
// Gold: 15 rows, primary column "sp.specNumber"

MATCH (sec:Section)-[:CONTAINS_TABLE]->(tbl:TSTable) WITH sec, count(tbl) AS tableCount WHERE tableCount >= 5 MATCH (sec)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, tableCount ORDER BY tableCount DESC LIMIT 15
