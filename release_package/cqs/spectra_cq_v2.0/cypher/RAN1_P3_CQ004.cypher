// SpectraCQ RAN1_P3_CQ004 (RAN1, phase 3) -- TS
// Question: Return the section count per level in TS 38.213 (gauging structural depth and complexity).
// Gold: 5 rows, primary column "sec.level"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.213'}) RETURN sec.level, count(sec) AS sectionCount ORDER BY sec.level
