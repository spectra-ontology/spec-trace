// SpectraCQ RAN2_P3_CQ1-8 (RAN2, phase 3) -- CQ1_TS
// Question: List all tables in spec 38.331 (table inventory).
// Gold: 24 rows, primary column "t.tableId"

MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber LIMIT 25
