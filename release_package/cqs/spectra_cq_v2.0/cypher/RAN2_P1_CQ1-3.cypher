// SpectraCQ RAN2_P1_CQ1-3 (RAN2, phase 1) -- CQ1_Tdoc
// Question: List the TDocs submitted by Huawei at meeting RAN2#132 (competitor contribution review).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10
