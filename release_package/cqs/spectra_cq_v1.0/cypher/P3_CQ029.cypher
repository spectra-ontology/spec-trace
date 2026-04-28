// SpectraCQ P3_CQ029 — 기술_키워드검색
// Question (English): Return sections whose titles contain 'antenna' (antenna-port spec locations).
// Schema area: classes=['Section', 'Spec'], rels=['BELONGS_TO_SPEC']

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*antenna.*' RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, sec.level ORDER BY sp.specNumber, sec.sectionNumber
