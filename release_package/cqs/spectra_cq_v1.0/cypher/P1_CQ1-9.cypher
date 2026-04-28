// SpectraCQ P1_CQ1-9 — CQ1_Tdoc기본검색
// Question (English): List the full agenda of meeting RAN1#120 with item descriptions (meeting preparation).
// Schema area: classes=['AgendaItem', 'Meeting', 'Tdoc'], rels=['BELONGS_TO', 'PRESENTED_AT']

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WITH DISTINCT a RETURN a.agendaNumber, a.agendaDescription ORDER BY a.agendaNumber ASC LIMIT 10
