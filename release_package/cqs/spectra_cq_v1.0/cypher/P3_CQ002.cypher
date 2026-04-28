// SpectraCQ P3_CQ002 — TS_구조탐색
// Question (English): Return the immediate sub-sections of TS 38.214 §5.1 (PDSCH-procedure implementation reference).
// Schema area: classes=['Section'], rels=['HAS_SUB_SECTION']

MATCH (root:Section {sectionId: '38.214-5.1'})-[:HAS_SUB_SECTION]->(sub:Section) RETURN sub.sectionNumber, sub.sectionTitle ORDER BY sub.sectionNumber
