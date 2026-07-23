// SpectraCQ RAN2_P1_CQ4-3 (RAN2, phase 1) -- CQ4
// Question: List the not-treated TDocs under Agenda Item 11.4.2 at RAN2#107 (pending-item backlog).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#107'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '11.4.2'}) WHERE t.status = 'not treated' RETURN t.tdocNumber, t.title, t.type ORDER BY t.tdocNumber ASC LIMIT 10
