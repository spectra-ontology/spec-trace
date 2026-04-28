// SpectraCQ P3_CQ014 — TS_참조분석
// Question (English): Return bidirectional reference pairs between sections (circular-dependency check).
// Schema area: classes=['Section', 'Spec'], rels=['BELONGS_TO_SPEC', 'REFERENCES_SECTION']

MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section)-[:REFERENCES_SECTION]->(a) WHERE id(a) < id(b) MATCH (a)-[:BELONGS_TO_SPEC]->(sp1:Spec) MATCH (b)-[:BELONGS_TO_SPEC]->(sp2:Spec) RETURN sp1.specNumber + '-' + a.sectionNumber AS sectionA, sp2.specNumber + '-' + b.sectionNumber AS sectionB LIMIT 20
