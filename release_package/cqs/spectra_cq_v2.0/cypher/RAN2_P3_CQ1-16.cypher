// SpectraCQ RAN2_P3_CQ1-16 (RAN2, phase 3) -- CQ1_TS
// Question: Return the top 5 sections by figure count (figure-dense sections).
// Gold: 5 rows, primary column "s.sectionId"

MATCH (s:Section)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN s.sectionId, count(f) AS figCount ORDER BY figCount DESC, s.sectionId LIMIT 5
