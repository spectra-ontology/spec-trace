// SpectraCQ RAN2_P2_CQ1-1 (RAN2, phase 2) -- CQ1_Resolution
// Question: List the agreements reached at meeting RAN2#117 (decision review).
// Gold: 15 rows, primary column "a.resolutionId"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#117'}) OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN a.resolutionId, a.content, ai.agendaNumber ORDER BY ai.agendaNumber, a.sequence LIMIT 15
