// SpectraCQ RAN2_P3_CQ1-7 (RAN2, phase 3) -- CQ1_TS
// Question: Which section contains Table 5.1-1 (table location)?
// Gold: 5 rows, primary column "t.tableId"

MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section) WHERE t.tableNumber = '5.1-1' RETURN t.tableId, s.sectionId, s.sectionTitle
