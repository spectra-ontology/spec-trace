// SpectraCQ RAN3_P2_CQ1-4 (RAN3, phase 2) -- CQ1_Resolution
// Question: List the resolutions under agenda item 8.1 (agenda-item decision history).
// Gold: 15 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '8.1'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, labels(r) AS types, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, r.sequence LIMIT 15
