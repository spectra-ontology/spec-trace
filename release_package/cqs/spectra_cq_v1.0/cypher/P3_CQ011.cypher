// SpectraCQ P3_CQ011 — TS_참조분석
// Question (English): Return the top-15 most-referenced sections across all 8 TSes.
// Schema area: classes=['Section', 'Spec'], rels=['BELONGS_TO_SPEC', 'REFERENCES_SECTION']

MATCH (tgt:Section)<-[:REFERENCES_SECTION]-(src:Section) WITH tgt, count(src) AS refByCnt MATCH (tgt)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, tgt.sectionNumber, tgt.sectionTitle, refByCnt ORDER BY refByCnt DESC LIMIT 15
