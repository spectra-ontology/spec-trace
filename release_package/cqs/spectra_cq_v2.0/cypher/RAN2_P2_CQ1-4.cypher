// SpectraCQ RAN2_P2_CQ1-4 (RAN2, phase 2) -- CQ1_Resolution
// Question: List the resolutions under Agenda Item 8.11 at RAN2#117 (agenda decision trace).
// Gold: 15 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WHERE (ai.agendaNumber = '8.11' OR ai.agendaNumber STARTS WITH '8.11.') AND ai.meetingNumber = '117' MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, labels(r) AS type, r.content ORDER BY r.sequence LIMIT 15
