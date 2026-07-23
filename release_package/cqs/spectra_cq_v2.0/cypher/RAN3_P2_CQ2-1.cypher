// SpectraCQ RAN3_P2_CQ2-1 (RAN3, phase 2) -- CQ2_Tdoc-Resolution
// Question: Return the TDocs referenced by three or more resolutions (high-impact contributions).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH t, count(r) AS refCnt WHERE refCnt >= 3 RETURN t.tdocNumber, refCnt ORDER BY refCnt DESC, t.tdocNumber LIMIT 10
