// SpectraCQ RAN4_P2_CQ2-4 (RAN4, phase 2) -- CQ2_Tdoc-Resolution
// Question: List the top 10 specs by resolution-linked TDocs (spec decision activity).
// Gold: 10 rows, primary column "s.specNumber"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN s.specNumber, count(DISTINCT t) AS tdocCnt ORDER BY tdocCnt DESC LIMIT 10
