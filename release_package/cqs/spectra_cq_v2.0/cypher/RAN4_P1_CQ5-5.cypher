// SpectraCQ RAN4_P1_CQ5-5 (RAN4, phase 1) -- 
// Question: List the top 10 specs by number of CRs (most-revised specs).
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS cnt ORDER BY cnt DESC LIMIT 10
