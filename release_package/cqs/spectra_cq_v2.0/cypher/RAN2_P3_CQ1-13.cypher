// SpectraCQ RAN2_P3_CQ1-13 (RAN2, phase 3) -- CQ1_TS
// Question: List the sections marked Void (placeholder scan).
// Gold: 15 rows, primary column "s.sectionId"

MATCH (s:Section) WHERE s.sectionTitle CONTAINS 'Void' OR s.sectionTitle CONTAINS 'void' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionId LIMIT 15
