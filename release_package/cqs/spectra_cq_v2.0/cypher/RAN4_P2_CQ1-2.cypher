// SpectraCQ RAN4_P2_CQ1-2 (RAN4, phase 2) -- CQ1_Resolution
// Question: List the conclusions drawn at meeting RAN4#98 (meeting outcome review).
// Gold: 1 rows, primary column "c.resolutionId"

MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN4#98'}) OPTIONAL MATCH (c)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN c.resolutionId, c.content, ai.agendaNumber, c.hasConsensus ORDER BY ai.agendaNumber, c.sequence LIMIT 15
