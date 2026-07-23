// SpectraCQ RAN4_P2_CQ2-1 (RAN4, phase 2) -- CQ2_Tdoc-Resolution
// Question: Which TDocs are referenced by 3 or more resolutions? (frequently cited documents).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH t, count(r) AS refCnt WHERE refCnt >= 3 RETURN t.tdocNumber, refCnt ORDER BY refCnt DESC, t.tdocNumber LIMIT 10
