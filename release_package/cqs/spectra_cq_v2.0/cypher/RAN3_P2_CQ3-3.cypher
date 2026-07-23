// SpectraCQ RAN3_P2_CQ3-3 (RAN3, phase 2) -- CQ3
// Question: Rank the main contributors to spec 38.423 (spec-ownership analysis).
// Gold: 10 rows, primary column "c.companyName"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.423'}) MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(DISTINCT t) AS cnt ORDER BY cnt DESC, c.companyName ASC LIMIT 10
