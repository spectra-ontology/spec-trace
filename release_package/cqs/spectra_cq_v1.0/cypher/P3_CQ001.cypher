// SpectraCQ P3_CQ001 — TS_구조탐색
// Question (English): Return the top-level table of contents of TS 38.214 (locating DL-scheduling content).
// Schema area: classes=['Section', 'Spec'], rels=['HAS_SECTION']

MATCH (sp:Spec {specNumber: '38.214'})-[:HAS_SECTION]->(sec:Section) RETURN sec.sectionNumber, sec.sectionTitle ORDER BY sec.sectionNumber
