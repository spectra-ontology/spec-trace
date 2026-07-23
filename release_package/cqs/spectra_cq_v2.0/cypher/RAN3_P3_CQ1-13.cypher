// SpectraCQ RAN3_P3_CQ1-13 (RAN3, phase 3) -- CQ1_TS
// Question: List the sections marked Void (deprecated-section survey).
// Gold: 15 rows, primary column "s.sectionId"

MATCH (s:Section) WHERE s.sectionTitle CONTAINS 'Void' OR s.sectionTitle CONTAINS 'void' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionId LIMIT 15
