// SpectraCQ RAN4_P2_CQ3-3 (RAN4, phase 2) -- CQ3
// Question: Rank the leading contributors to spec 38.133 (key contributors to a spec).
// Gold: 10 rows, primary column "c.companyName"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.133'}) MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(DISTINCT t) AS cnt ORDER BY cnt DESC, c.companyName ASC LIMIT 10
