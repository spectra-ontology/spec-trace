// SpectraCQ RAN4_P3_CQ3-7 (RAN4, phase 3) -- CQ3_CR
// Question: List the top 10 companies that modify spec 38.133 the most (leading change contributors).
// Gold: 10 rows, primary column "c.companyName"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
