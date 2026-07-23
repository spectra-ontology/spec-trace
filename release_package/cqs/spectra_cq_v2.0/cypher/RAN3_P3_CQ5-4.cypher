// SpectraCQ RAN3_P3_CQ5-4 (RAN3, phase 3) -- CQ5
// Question: Show the distribution of table counts per spec (tabular-content profile).
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(t) AS tblCnt ORDER BY tblCnt DESC LIMIT 5
