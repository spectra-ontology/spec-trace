// SpectraCQ P3_CQ006 — TS_구조탐색
// Question (English): List all tables defined in TS 38.214 (parameter-table reference for implementation).
// Schema area: classes=['Section', 'Spec', 'TSTable'], rels=['BELONGS_TO_SPEC', 'TABLE_IN_SECTION']

MATCH (tbl:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.214'}) RETURN tbl.tableNumber, tbl.tableCaption, sec.sectionNumber ORDER BY tbl.tableNumber
