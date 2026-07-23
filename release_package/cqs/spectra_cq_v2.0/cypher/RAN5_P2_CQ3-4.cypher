// SpectraCQ RAN5_P2_CQ3-4 (RAN5, phase 2) -- CQ3
// Question: Compare Samsung and Qualcomm by resolution contribution (head-to-head comparison).
// Gold: 2 rows, primary column "company"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WHERE c.companyName IN ['Samsung', 'Qualcomm'] WITH c.companyName AS company, count(DISTINCT r) AS cnt RETURN company, cnt ORDER BY cnt DESC
