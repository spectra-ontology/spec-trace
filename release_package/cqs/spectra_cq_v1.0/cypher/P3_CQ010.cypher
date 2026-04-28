// SpectraCQ P3_CQ010 — TS_참조분석
// Question (English): Return the sections that reference TS 38.211 §5.2.1 (Pseudo-random sequence) — base-algorithm dependents.
// Schema area: classes=['Section'], rels=['REFERENCES_SECTION']

MATCH (tgt:Section {sectionId: '38.211-5.2.1'})<-[:REFERENCES_SECTION]-(src:Section) RETURN src.sectionNumber, src.sectionTitle ORDER BY src.sectionNumber LIMIT 30
