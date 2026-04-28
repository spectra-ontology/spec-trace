// SpectraCQ P3_CQ012 — TS_참조분석
// Question (English): Return mutually-referencing section pairs in TS 38.213 (closely-coupled procedures).
// Schema area: classes=['Section'], rels=['REFERENCES_SECTION']

MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section)-[:REFERENCES_SECTION]->(a) WHERE a.sectionId STARTS WITH '38.213' AND b.sectionId STARTS WITH '38.213' AND a.sectionId < b.sectionId RETURN a.sectionNumber AS sectionA, a.sectionTitle AS titleA, b.sectionNumber AS sectionB, b.sectionTitle AS titleB LIMIT 20
