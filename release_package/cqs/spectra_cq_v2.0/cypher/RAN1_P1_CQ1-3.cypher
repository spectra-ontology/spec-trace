// SpectraCQ RAN1_P1_CQ1-3 (RAN1, phase 1) -- CQ1_Tdoc
// Question: List the TDocs submitted by Huawei at meeting RAN1#120 (tracking a competitor's contributions).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
