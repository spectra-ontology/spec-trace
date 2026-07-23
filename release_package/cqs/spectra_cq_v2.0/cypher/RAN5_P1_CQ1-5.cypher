// SpectraCQ RAN5_P1_CQ1-5 (RAN5, phase 1) -- 
// Question: List Samsung's TDocs, newest first (contributor tracking).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName:'Samsung'}) RETURN t.tdocNumber ORDER BY t.tdocNumber DESC LIMIT 10
