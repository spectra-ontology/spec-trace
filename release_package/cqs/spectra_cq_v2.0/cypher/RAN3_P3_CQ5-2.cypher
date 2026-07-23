// SpectraCQ RAN3_P3_CQ5-2 (RAN3, phase 3) -- CQ5
// Question: Return the top 5 specs by CR count (most-changed specs).
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crs ORDER BY crs DESC LIMIT 5
