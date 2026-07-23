// SpectraCQ RAN3_P2_CQ3-2 (RAN3, phase 2) -- CQ3
// Question: Return the top 10 companies by resolution contribution (influence ranking).
// Gold: 10 rows, primary column "c.companyName"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(DISTINCT r) AS cnt ORDER BY cnt DESC, c.companyName ASC LIMIT 10
