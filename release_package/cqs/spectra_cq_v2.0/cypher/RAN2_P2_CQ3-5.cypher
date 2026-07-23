// SpectraCQ RAN2_P2_CQ3-5 (RAN2, phase 2) -- CQ3
// Question: Rank the top 10 companies by resolution-referenced TDocs (overall influence).
// Gold: 10 rows, primary column "c.companyName"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (r)-[:MADE_AT]->(m:Meeting) RETURN c.companyName, count(DISTINCT r) AS resolutionCount ORDER BY resolutionCount DESC LIMIT 10
