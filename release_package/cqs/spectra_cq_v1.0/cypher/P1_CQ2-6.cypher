// SpectraCQ P1_CQ2-6 — CQ2_Tdoc관계추적
// Question (English): List the TDocs at meeting RAN1#120 that were postponed to the next meeting (open-issue tracking).
// Schema area: classes=['Meeting', 'Tdoc'], rels=['PRESENTED_AT']

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc {status: 'postponed'}) RETURN t.tdocNumber, t.title, t.type ORDER BY t.tdocNumber ASC LIMIT 10
