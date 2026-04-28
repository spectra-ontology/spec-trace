// SpectraCQ P3_CQ004 — TS_구조탐색
// Question (English): Return the per-level section count of TS 38.213 (structural-complexity profile).
// Schema area: classes=['Section', 'Spec'], rels=['BELONGS_TO_SPEC']

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.213'}) RETURN sec.level, count(sec) AS sectionCount ORDER BY sec.level
