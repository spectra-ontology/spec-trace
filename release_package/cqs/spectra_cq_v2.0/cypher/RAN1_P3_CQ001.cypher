// SpectraCQ RAN1_P3_CQ001 (RAN1, phase 3) -- TS
// Question: Return the top-level table of contents of TS 38.214 (locating DL-scheduling content).
// Gold: 46 rows, primary column "sec.sectionNumber"

MATCH (sp:Spec {specNumber: '38.214'})-[:HAS_SECTION]->(sec:Section) RETURN sec.sectionNumber, sec.sectionTitle ORDER BY sec.sectionNumber
