// SpectraCQ RAN3_P1_CQ1-9 (RAN3, phase 1) -- CQ1_Tdoc
// Question: List all agenda items covered at meeting RAN3#130 (meeting-scope overview).
// Gold: 10 rows, primary column "a.agendaNumber"

MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}), (t)-[:BELONGS_TO]->(a:AgendaItem) RETURN DISTINCT a.agendaNumber, a.agendaDescription ORDER BY a.agendaNumber LIMIT 10
