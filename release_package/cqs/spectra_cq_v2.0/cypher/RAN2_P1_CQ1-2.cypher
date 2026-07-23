// SpectraCQ RAN2_P1_CQ1-2 (RAN2, phase 1) -- CQ1_Tdoc
// Question: List the TDocs under Agenda Item 6.1.3.1 (NR RRC) at meeting RAN2#132 (RRC agenda scan).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '6.1.3.1'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10
