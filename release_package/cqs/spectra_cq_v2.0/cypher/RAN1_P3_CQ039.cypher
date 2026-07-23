// SpectraCQ RAN1_P3_CQ039 (RAN1, phase 3) -- 
// Question: Which companies submitted the most CRs modifying TS 38.214? Top 10 (technical leadership in this spec).
// Gold: 10 rows, primary column "co.companyName"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) MATCH (cr)-[:SUBMITTED_BY]->(co:Company) RETURN co.companyName, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
