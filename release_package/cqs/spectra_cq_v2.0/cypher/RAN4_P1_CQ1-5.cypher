// SpectraCQ RAN4_P1_CQ1-5 (RAN4, phase 1) -- 
// Question: List Huawei's TDocs (per-company contribution overview).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName:'Huawei'}) RETURN t.tdocNumber ORDER BY t.tdocNumber DESC LIMIT 10
