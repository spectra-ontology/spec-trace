// SpectraCQ RAN1_P2_CQ3-5 (RAN1, phase 2) -- CQ3
// Question: Compare Ericsson's and Nokia's contributions to resolutions.
// Gold: 2 rows, primary column "c.companyName"

MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WHERE c.companyName IN ['Ericsson', 'Nokia'] RETURN c.companyName, count(DISTINCT a) AS contributionCount ORDER BY contributionCount DESC
