// SpectraCQ P3_CQ035 — technical_keyword_search
// Question (English): Return sections containing measurement or reporting keywords (measurement-reporting scope).
// Schema area: classes=['Section', 'Spec'], rels=['BELONGS_TO_SPEC']

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*(measurement|reporting).*' RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle ORDER BY sp.specNumber, sec.sectionNumber LIMIT 20
