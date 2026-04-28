// SpectraCQ P3_CQ005 — TS_구조탐색
// Question (English): Return the section in TS 38.213 with the most embedded tables (parameter-dense implementation hotspot).
// Schema area: classes=['Section', 'Spec', 'TSTable'], rels=['BELONGS_TO_SPEC', 'CONTAINS_TABLE']

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.213'}) MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sec.sectionNumber, sec.sectionTitle, count(tbl) AS tableCount ORDER BY tableCount DESC LIMIT 15
