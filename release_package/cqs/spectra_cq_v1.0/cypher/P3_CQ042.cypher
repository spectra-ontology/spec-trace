// SpectraCQ P3_CQ042 — 통합분석
// Question (English): Return the top-10 sections with both many sub-sections and tables (high-complexity areas).
// Schema area: classes=['Section', 'Spec', 'TSTable'], rels=['BELONGS_TO_SPEC', 'CONTAINS_TABLE', 'HAS_SUB_SECTION']

MATCH (sec:Section)-[:CONTAINS_TABLE]->(tbl:TSTable) WITH sec, count(tbl) AS tableCount WHERE tableCount >= 3 MATCH (sec)-[:BELONGS_TO_SPEC]->(sp:Spec) OPTIONAL MATCH (sec)-[:HAS_SUB_SECTION]->(sub:Section) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, tableCount, count(sub) AS subSectionCount ORDER BY tableCount DESC LIMIT 10
