// SpectraCQ RAN4_P2_CQ3-2 (RAN4, phase 2) -- CQ3
// Question: List the top 10 companies by resolution contributions (leading decision contributors).
// Gold: 10 rows, primary column "c.companyName"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(DISTINCT r) AS cnt ORDER BY cnt DESC, c.companyName ASC LIMIT 10
