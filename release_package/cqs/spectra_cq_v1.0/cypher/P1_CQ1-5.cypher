// SpectraCQ P1_CQ1-5 — CQ1_Tdoc기본검색
// Question (English): List the TDocs at meeting RAN1#121 with status approved or agreed.
// Schema area: classes=['Meeting', 'Tdoc'], rels=['PRESENTED_AT']

MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status IN ['approved', 'agreed'] RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
