// SpectraCQ RAN4_P2_CQ3-4 (RAN4, phase 2) -- CQ3
// Question: Compare Samsung's and Qualcomm's resolution contributions (head-to-head activity).
// Gold: 2 rows, primary column "c.companyName"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WHERE c.companyName IN ['Samsung', 'Qualcomm'] RETURN c.companyName, count(DISTINCT r) AS cnt ORDER BY cnt DESC
