// SpectraCQ RAN3_P3_CQ1-9 (RAN3, phase 3) -- CQ1_TS
// Question: List the sections whose title contains 'handover' (topic-based section search).
// Gold: 10 rows, primary column "sec.sectionId"

MATCH (sec:Section) WHERE toLower(sec.sectionTitle) CONTAINS 'handover' RETURN sec.sectionId, sec.sectionTitle ORDER BY sec.sectionId LIMIT 10
