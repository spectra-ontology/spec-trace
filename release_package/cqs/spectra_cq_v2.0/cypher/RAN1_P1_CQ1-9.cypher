// SpectraCQ RAN1_P1_CQ1-9 (RAN1, phase 1) -- CQ1_Tdoc
// Question: List the full agenda of meeting RAN1#120 with descriptions (meeting preparation).
// Gold: 10 rows, primary column "a.agendaNumber"

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WITH DISTINCT a RETURN a.agendaNumber, a.agendaDescription ORDER BY a.agendaNumber ASC LIMIT 10
