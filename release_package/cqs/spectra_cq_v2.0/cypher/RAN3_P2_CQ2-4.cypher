// SpectraCQ RAN3_P2_CQ2-4 (RAN3, phase 2) -- CQ2_Tdoc-Resolution
// Question: Count resolution-referenced TDocs per spec they modify (spec-change tracing).
// Gold: 10 rows, primary column "s.specNumber"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN s.specNumber, count(DISTINCT t) AS tdocCnt ORDER BY tdocCnt DESC LIMIT 10
