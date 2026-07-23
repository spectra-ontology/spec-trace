// SpectraCQ RAN4_P2_CQ1-4 (RAN4, phase 2) -- CQ1_Resolution
// Question: List the resolutions under agenda item 7 (agenda-scoped decisions).
// Gold: 3 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '7'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, labels(r) AS types, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, r.sequence LIMIT 15
