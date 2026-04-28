// SpectraCQ P3_CQ041 — 통합분석
// Question (English): Return sections with 5+ embedded tables (parameter-dense implementation hotspots).
// Schema area: classes=['Section', 'Spec', 'TSTable'], rels=['BELONGS_TO_SPEC', 'CONTAINS_TABLE']

MATCH (sec:Section)-[:CONTAINS_TABLE]->(tbl:TSTable) WITH sec, count(tbl) AS tableCount WHERE tableCount >= 5 MATCH (sec)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, tableCount ORDER BY tableCount DESC LIMIT 15
