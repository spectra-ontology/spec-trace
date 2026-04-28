// SpectraCQ P1_CQ1-2 — CQ1_Tdoc기본검색
// Question (English): List the TDocs presented at meeting RAN1#121 under agenda items beginning with 9.2 (AI/ML for NR session preparation).
// Schema area: classes=['AgendaItem', 'Meeting', 'Tdoc'], rels=['BELONGS_TO', 'PRESENTED_AT']

MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE a.agendaNumber STARTS WITH '9.2' RETURN t.tdocNumber, t.title, t.type, a.agendaNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
