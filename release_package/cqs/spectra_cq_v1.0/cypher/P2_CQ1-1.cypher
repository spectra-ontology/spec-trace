// SpectraCQ P2_CQ1-1 — CQ1_Resolution조회
// Question (English): List the Agreements made at meeting RAN1#115 under agenda items beginning with 7.1 (NR MIMO outcome review).
// Schema area: classes=['AgendaItem', 'Agreement', 'Meeting', 'RESOLUTION_BELONGS_TO'], rels=['MADE_AT', 'RESOLUTION_BELONGS_TO']

MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) WHERE ai.agendaNumber STARTS WITH '7.1' RETURN a.resolutionId, a.content, ai.agendaNumber ORDER BY ai.agendaNumber, a.sequence LIMIT 15
