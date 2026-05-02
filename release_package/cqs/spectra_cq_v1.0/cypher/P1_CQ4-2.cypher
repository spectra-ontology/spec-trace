// SpectraCQ P1_CQ4-2 — CQ4_회의히스토리
// Question (English): Summarize Ericsson's TDoc outcomes at meeting RAN1#120 by status.
// Schema area: classes=['Company', 'Meeting', 'Tdoc'], rels=['PRESENTED_AT', 'SUBMITTED_BY']

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Ericsson'}) RETURN t.status, count(t) AS count ORDER BY count DESC LIMIT 10
