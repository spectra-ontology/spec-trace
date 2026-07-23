// SpectraCQ RAN1_P3_CQ006 (RAN1, phase 3) -- TS
// Question: List all tables defined in TS 38.214 (parameter tables to reference during implementation).
// Gold: 548 rows, primary column "tbl.tableNumber"

MATCH (tbl:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.214'}) RETURN tbl.tableNumber, tbl.tableCaption, sec.sectionNumber ORDER BY tbl.tableNumber
