// SpectraCQ RAN3_P3_CQ1-8 (RAN3, phase 3) -- CQ1_TS
// Question: List all tables in spec 38.423 (tabular-content inventory).
// Gold: 10 rows, primary column "t.tableId"

MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber LIMIT 25
