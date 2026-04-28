// SpectraCQ P2_CQ1-2 — CQ1_Resolution조회
// Question (English): Return the Agreements at meeting RAN1#100 on agenda item 5.1 (UL Tx switching technical decisions).
// Schema area: classes=['AgendaItem', 'Agreement', 'Meeting', 'RESOLUTION_BELONGS_TO'], rels=['MADE_AT', 'RESOLUTION_BELONGS_TO']

MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '5.1'}), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#100'}) RETURN a.resolutionId, a.content ORDER BY a.sequence LIMIT 10
