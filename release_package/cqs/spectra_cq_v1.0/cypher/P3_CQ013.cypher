// SpectraCQ P3_CQ013 — TS_참조분석
// Question (English): Compare cross-reference density per TS (inter-section-reference tightness).
// Schema area: classes=['Section', 'Spec'], rels=['BELONGS_TO_SPEC', 'REFERENCES_SECTION']

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WITH sp.specNumber AS ts, count(sec) AS secCnt OPTIONAL MATCH (src:Section)-[:REFERENCES_SECTION]->(tgt:Section) WHERE src.sectionId STARTS WITH ts WITH ts, secCnt, count(*) AS refCnt RETURN ts, secCnt, refCnt, round(toFloat(refCnt) / secCnt * 100) / 100 AS refDensity ORDER BY refDensity DESC
