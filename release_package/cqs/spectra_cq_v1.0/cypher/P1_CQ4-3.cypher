// SpectraCQ P1_CQ4-3 — CQ4_회의히스토리
// Question (English): List TDocs at meeting RAN1#120 on agenda item 9.3 (NR duplex evolution) that remain not treated (open-issue review).
// Schema area: classes=['AgendaItem', 'Meeting', 'Tdoc'], rels=['BELONGS_TO', 'PRESENTED_AT']

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE a.agendaNumber STARTS WITH '9.3' AND t.status = 'not treated' RETURN t.tdocNumber, t.title, a.agendaNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
