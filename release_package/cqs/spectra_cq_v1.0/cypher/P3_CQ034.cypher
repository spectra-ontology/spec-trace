// SpectraCQ P3_CQ034 — 기술_키워드검색
// Question (English): Return SRS-related sections and tables (Sounding Reference Signal scope).
// Schema area: classes=['Section', 'Spec', 'TSTable'], rels=['BELONGS_TO_SPEC', 'CONTAINS_TABLE']

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*SRS.*' OR sec.sectionTitle =~ '(?i).*sounding.*' OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, collect(tbl.tableNumber) AS tables ORDER BY sp.specNumber, sec.sectionNumber
