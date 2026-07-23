// SpectraCQ RAN2_P2_CQ3-4 (RAN2, phase 2) -- CQ3
// Question: Compare resolution contributions between Huawei and Ericsson (head-to-head).
// Gold: 2 rows, primary column "c.companyName"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WHERE c.companyName IN ['Huawei', 'Ericsson'] RETURN c.companyName, count(DISTINCT r) AS resolutionCount ORDER BY resolutionCount DESC
