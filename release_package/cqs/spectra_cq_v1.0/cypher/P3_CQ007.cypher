// SpectraCQ P3_CQ007 — TS_구조탐색
// Question (English): List sections with 'PDSCH' in the title across all TSes.
// Schema area: classes=['Section', 'Spec'], rels=['BELONGS_TO_SPEC']

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PDSCH.*' RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, sec.level ORDER BY sp.specNumber, sec.sectionNumber
