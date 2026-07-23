// SpectraCQ RAN1_P2_CQ1-1 (RAN1, phase 2) -- CQ1_Resolution
// Question: List the agreements under Agenda Item 7.1 (NR MIMO) at meeting RAN1#115 (MIMO meeting outcomes).
// Gold: 11 rows, primary column "a.resolutionId"

MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) WHERE ai.agendaNumber STARTS WITH '7.1' RETURN a.resolutionId, a.content, ai.agendaNumber ORDER BY ai.agendaNumber, a.sequence LIMIT 15
