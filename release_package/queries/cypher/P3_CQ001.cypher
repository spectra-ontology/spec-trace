// P3_CQ001 — Phase 3 (TS structure)
// Return the top-level section table of contents of TS 38.214.

MATCH (sp:Spec {specNumber: '38.214'})-[:HAS_SECTION]->(sec:Section) RETURN sec.sectionNumber, sec.sectionTitle ORDER BY sec.sectionNumber
