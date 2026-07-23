// SpectraCQ RAN5_P3_CQ1-7 (RAN5, phase 3) -- CQ1_TS
// Question: Find which sections contain tables in TS 38.521-1 (table-to-section mapping).
// Gold: 5 rows, primary column "t.tableId"

MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-1'}) RETURN t.tableId, sec.sectionId, sec.sectionTitle ORDER BY t.tableNumber, t.tableId LIMIT 5
