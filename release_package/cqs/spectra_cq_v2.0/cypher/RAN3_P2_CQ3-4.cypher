// SpectraCQ RAN3_P2_CQ3-4 (RAN3, phase 2) -- CQ3
// Question: Compare ZTE's and Huawei's resolution contributions (head-to-head influence).
// Gold: 2 rows, primary column "c.companyName"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WHERE c.companyName IN ['ZTE', 'Huawei'] RETURN c.companyName, count(DISTINCT r) AS cnt ORDER BY cnt DESC
