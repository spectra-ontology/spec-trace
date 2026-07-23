// SpectraCQ RAN5_P3_CQ5-5 (RAN5, phase 3) -- CQ5
// Question: How many sections do RAN5 specs contain in total? (corpus size)
// Gold: 1 rows, primary column "totalSections"

MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(s) AS totalSections
