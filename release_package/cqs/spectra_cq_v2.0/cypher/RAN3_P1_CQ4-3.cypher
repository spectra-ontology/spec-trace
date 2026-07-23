// SpectraCQ RAN3_P1_CQ4-3 (RAN3, phase 1) -- CQ4
// Question: List the not-treated TDocs under agenda item 13.2 at meeting RAN3#122 (pending-item tracking).
// Gold: 2 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '13.2'}), (t)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 122}) WHERE t.status = 'not treated' RETURN t.tdocNumber, t.title LIMIT 10
