// SpectraCQ P3_CQ015 — TS_참조분석
// Question (English): Return the 2-hop dependencies of TS 38.214 §5.1 (transitive references).
// Schema area: classes=['Section', 'Spec'], rels=['BELONGS_TO_SPEC', 'REFERENCES_SECTION']

MATCH (start:Section {sectionId: '38.214-5.1'})-[:REFERENCES_SECTION]->(mid:Section)-[:REFERENCES_SECTION]->(end:Section) MATCH (mid)-[:BELONGS_TO_SPEC]->(sp1:Spec) MATCH (end)-[:BELONGS_TO_SPEC]->(sp2:Spec) RETURN sp1.specNumber + '-' + mid.sectionNumber AS via, sp2.specNumber + '-' + end.sectionNumber AS target, end.sectionTitle LIMIT 20
