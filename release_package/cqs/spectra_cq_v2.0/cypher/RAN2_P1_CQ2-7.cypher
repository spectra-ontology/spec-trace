// SpectraCQ RAN2_P1_CQ2-7 (RAN2, phase 1) -- CQ2_Tdoc
// Question: List the incoming liaison statements at meeting RAN2#132 with their agenda items (incoming-LS triage).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:LS)-[:BELONGS_TO]->(a:AgendaItem) WHERE t.direction = 'in' RETURN t.tdocNumber, t.title, a.agendaNumber ORDER BY a.agendaNumber ASC, t.tdocNumber LIMIT 10
