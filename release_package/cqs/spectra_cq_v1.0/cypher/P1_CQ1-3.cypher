// SpectraCQ P1_CQ1-3 — CQ1_Tdoc기본검색
// Question (English): List the TDocs submitted at meeting RAN1#120 by Huawei (competitor-contribution trend analysis).
// Schema area: classes=['Company', 'Meeting', 'Tdoc'], rels=['PRESENTED_AT', 'SUBMITTED_BY']

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
