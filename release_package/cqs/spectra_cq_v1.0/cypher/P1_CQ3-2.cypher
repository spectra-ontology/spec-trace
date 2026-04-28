// SpectraCQ P1_CQ3-2 — CQ3_회사분석
// Question (English): List TDocs from other companies on agenda item 8.1 (NR Coverage Enhancement) at meeting RAN1#120 (competitor contribution review).
// Schema area: classes=['AgendaItem', 'Company', 'Meeting', 'Tdoc'], rels=['BELONGS_TO', 'PRESENTED_AT', 'SUBMITTED_BY']

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE a.agendaNumber STARTS WITH '8.1' MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN t.tdocNumber, t.title, c.companyName, a.agendaNumber ORDER BY t.tdocNumber ASC LIMIT 10
