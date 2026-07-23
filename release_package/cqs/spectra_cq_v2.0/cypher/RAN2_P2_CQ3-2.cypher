// SpectraCQ RAN2_P2_CQ3-2 (RAN2, phase 2) -- CQ3
// Question: Rank the main contributors to spec 38.331 (RRC ownership).
// Gold: 10 rows, primary column "c.companyName"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}), (t)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(DISTINCT r) AS contributions ORDER BY contributions DESC LIMIT 10
