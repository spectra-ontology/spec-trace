// SpectraCQ RAN2_P3_CQ5-4 (RAN2, phase 3) -- CQ5
// Question: Return the distribution of table counts across specs (table density).
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(t) AS tblCnt ORDER BY tblCnt DESC LIMIT 5
