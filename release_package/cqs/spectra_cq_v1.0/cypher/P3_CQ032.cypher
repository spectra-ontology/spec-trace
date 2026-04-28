// SpectraCQ P3_CQ032 — 기술_키워드검색
// Question (English): Return PDCCH-related sections and tables (control-channel implementation scope).
// Schema area: classes=['Section', 'Spec', 'TSTable'], rels=['BELONGS_TO_SPEC', 'CONTAINS_TABLE']

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PDCCH.*' OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, sec.level, collect(tbl.tableNumber) AS tables ORDER BY sp.specNumber, sec.sectionNumber
