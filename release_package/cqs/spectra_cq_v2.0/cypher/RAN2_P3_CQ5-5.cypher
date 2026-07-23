// SpectraCQ RAN2_P3_CQ5-5 (RAN2, phase 3) -- CQ5
// Question: Return the distribution of figure counts across specs (figure density).
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (f:TSFigure)-[:FIGURE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(f) AS figCnt ORDER BY figCnt DESC LIMIT 5
