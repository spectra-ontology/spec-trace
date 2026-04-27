// P3_CQ002 — Phase 3 (TS structure)
// Return the immediate sub-sections of TS 38.214 section 5.1.

MATCH (root:Section {sectionId: '38.214-5.1'})-[:HAS_SUB_SECTION]->(sub:Section) RETURN sub.sectionNumber, sub.sectionTitle ORDER BY sub.sectionNumber
