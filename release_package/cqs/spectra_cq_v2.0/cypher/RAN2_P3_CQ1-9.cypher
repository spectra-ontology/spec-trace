// SpectraCQ RAN2_P3_CQ1-9 (RAN2, phase 3) -- CQ1_TS
// Question: List the sections whose title contains 'MAC' (topic search).
// Gold: 25 rows, primary column "s.sectionId"

MATCH (s:Section) WHERE s.sectionTitle CONTAINS 'MAC' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionId LIMIT 25
