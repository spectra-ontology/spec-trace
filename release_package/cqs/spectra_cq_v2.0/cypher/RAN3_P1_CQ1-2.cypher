// SpectraCQ RAN3_P1_CQ1-2 (RAN3, phase 1) -- CQ1_Tdoc
// Question: List the TDocs under agenda item 8.1 at meeting RAN3#130 (agenda-item document review).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.1'}), (t)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}) RETURN t.tdocNumber, t.title, t.status ORDER BY t.tdocNumber LIMIT 10
