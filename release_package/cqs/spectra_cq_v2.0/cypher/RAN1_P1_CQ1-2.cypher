// SpectraCQ RAN1_P1_CQ1-2 (RAN1, phase 1) -- CQ1_Tdoc
// Question: List the TDocs under Agenda Item 9.2 (AI/ML for NR) at meeting RAN1#121 (AI/ML session preparation).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE a.agendaNumber STARTS WITH '9.2' RETURN t.tdocNumber, t.title, t.type, a.agendaNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
