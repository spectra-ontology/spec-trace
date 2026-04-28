// SpectraCQ P3_CQ031 — 기술_키워드검색
// Question (English): Return sections containing 'HARQ' across TSes (HARQ-process implementation scope).
// Schema area: classes=['Section', 'Spec'], rels=['BELONGS_TO_SPEC']

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*HARQ.*' RETURN sp.specNumber, count(sec) AS sectionCount, collect(sec.sectionNumber) AS sections ORDER BY sectionCount DESC
