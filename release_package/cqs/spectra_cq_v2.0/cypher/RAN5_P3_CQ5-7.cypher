// SpectraCQ RAN5_P3_CQ5-7 (RAN5, phase 3) -- CQ5
// Question: How many figures do RAN5 specs contain in total? (figure corpus size)
// Gold: 1 rows, primary column "totalFigures"

MATCH (f:TSFigure)-[:FIGURE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(f) AS totalFigures
