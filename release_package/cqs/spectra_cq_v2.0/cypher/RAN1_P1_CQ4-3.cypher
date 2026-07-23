// SpectraCQ RAN1_P1_CQ4-3 (RAN1, phase 1) -- CQ4
// Question: List the TDocs still not treated under Agenda Item 9.3 (NR duplex evolution) at meeting RAN1#120.
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE a.agendaNumber STARTS WITH '9.3' AND t.status = 'not treated' RETURN t.tdocNumber, t.title, a.agendaNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
