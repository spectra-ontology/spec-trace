// SpectraCQ P3_CQ033 — 기술_키워드검색
// Question (English): Return PUSCH-related sections and tables (uplink-data-channel implementation scope).
// Schema area: classes=['Section', 'Spec', 'TSTable'], rels=['BELONGS_TO_SPEC', 'CONTAINS_TABLE']

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PUSCH.*' OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, collect(tbl.tableNumber) AS tables ORDER BY sp.specNumber, sec.sectionNumber
