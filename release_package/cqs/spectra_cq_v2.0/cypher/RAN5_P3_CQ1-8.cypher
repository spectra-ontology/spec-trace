// SpectraCQ RAN5_P3_CQ1-8 (RAN5, phase 3) -- CQ1_TS
// Question: List all tables in TS 38.523-1 (table inventory).
// Gold: 25 rows, primary column "t.tableId"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.523-1'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber, t.tableId LIMIT 25
