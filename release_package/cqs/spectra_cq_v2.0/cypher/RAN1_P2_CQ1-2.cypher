// SpectraCQ RAN1_P2_CQ1-2 (RAN1, phase 2) -- CQ1_Resolution
// Question: What was agreed on UL Tx switching (Agenda 5.1) at meeting RAN1#100? (UL switching decisions)
// Gold: 6 rows, primary column "a.resolutionId"

MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '5.1'}), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#100'}) RETURN a.resolutionId, a.content ORDER BY a.sequence LIMIT 10
