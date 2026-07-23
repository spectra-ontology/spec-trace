// SpectraCQ RAN3_P3_CQ5-5 (RAN3, phase 3) -- CQ5
// Question: Show the distribution of figure counts per spec (figure-content profile).
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (f:TSFigure)-[:FIGURE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(f) AS figCnt ORDER BY figCnt DESC LIMIT 5
