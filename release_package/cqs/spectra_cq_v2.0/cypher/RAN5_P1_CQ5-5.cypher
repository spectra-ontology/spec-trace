// SpectraCQ RAN5_P1_CQ5-5 (RAN5, phase 1) -- 
// Question: Which ten specs receive the most CRs? (spec churn ranking)
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS cnt ORDER BY cnt DESC LIMIT 10
