// P2_CQ1-2 — Phase 2 (Resolution lookup)
// List the Agreements made at meeting RAN1#100 under agenda item 5.1.

MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '5.1'}), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#100'}) RETURN a.resolutionId, a.content ORDER BY a.sequence LIMIT 10
