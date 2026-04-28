// SpectraCQ P3_CQ030 — 기술_키워드검색
// Question (English): List CSI-related tables (parameter tables for CSI reporting).
// Schema area: classes=['Section', 'Spec', 'TSTable'], rels=['BELONGS_TO_SPEC', 'TABLE_IN_SECTION']

MATCH (tbl:TSTable) WHERE tbl.tableCaption =~ '(?i).*CSI.*' MATCH (tbl)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, tbl.tableNumber, tbl.tableCaption, sec.sectionNumber ORDER BY sp.specNumber, tbl.tableNumber LIMIT 20
