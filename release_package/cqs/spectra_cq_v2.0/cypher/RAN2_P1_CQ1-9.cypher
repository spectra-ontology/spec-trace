// SpectraCQ RAN2_P1_CQ1-9 (RAN2, phase 1) -- CQ1_Tdoc
// Question: List all agenda items and their descriptions for meeting RAN2#132 (agenda overview).
// Gold: 50 rows, primary column "a.agendaNumber"

MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WITH DISTINCT a RETURN a.agendaNumber, a.agendaDescription ORDER BY a.agendaNumber ASC LIMIT 50
