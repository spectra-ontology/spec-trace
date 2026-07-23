// SpectraCQ RAN1_P3_CQ005 (RAN1, phase 3) -- TS
// Question: Which sections of TS 38.213 contain the most tables? (finding parameter-dense implementation points)
// Gold: 15 rows, primary column "sec.sectionNumber"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.213'}) MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sec.sectionNumber, sec.sectionTitle, count(tbl) AS tableCount ORDER BY tableCount DESC LIMIT 15
