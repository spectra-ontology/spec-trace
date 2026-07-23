// SpectraCQ RAN5_P3_CQ5-6 (RAN5, phase 3) -- CQ5
// Question: How many tables do RAN5 specs contain in total? (table corpus size)
// Gold: 1 rows, primary column "totalTables"

MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(t) AS totalTables
