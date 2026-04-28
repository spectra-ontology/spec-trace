// SpectraCQ P3_CQ009 — TS_참조분석
// Question (English): Return the cross-references for TS 38.214 §5.1 (which sections must be co-read during implementation).
// Schema area: classes=['Section'], rels=['REFERENCES_SECTION']

MATCH (src:Section {sectionId: '38.214-5.1'})-[:REFERENCES_SECTION]->(tgt:Section) RETURN tgt.sectionNumber, tgt.sectionTitle ORDER BY tgt.sectionNumber
