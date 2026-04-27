// P3_CQ004 — Phase 3 (TS structure)
// Return the per-level section count for TS 38.213 (structural complexity profile).

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.213'}) RETURN sec.level, count(sec) AS sectionCount ORDER BY sec.level
