// SpectraCQ RAN5_P3_CQ5-4 (RAN5, phase 3) -- CQ5
// Question: Which five RAN5 specs received the most CRs? (highest-churn specs)
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 5
