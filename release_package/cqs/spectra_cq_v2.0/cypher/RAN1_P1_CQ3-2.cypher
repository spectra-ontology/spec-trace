// SpectraCQ RAN1_P1_CQ3-2 (RAN1, phase 1) -- CQ3
// Question: List other companies' TDocs under Agenda Item 8.1 (NR Coverage Enhancement) at meeting RAN1#120 (surveying competitors).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE a.agendaNumber STARTS WITH '8.1' MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN t.tdocNumber, t.title, c.companyName, a.agendaNumber ORDER BY t.tdocNumber ASC LIMIT 10
