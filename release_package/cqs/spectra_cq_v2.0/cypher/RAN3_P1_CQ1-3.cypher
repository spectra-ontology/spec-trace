// SpectraCQ RAN3_P1_CQ1-3 (RAN3, phase 1) -- CQ1_Tdoc
// Question: List the TDocs Huawei submitted at meeting RAN3#130 (tracking a company's contributions).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}), (t)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN t.tdocNumber, t.title, t.type ORDER BY t.tdocNumber LIMIT 10
