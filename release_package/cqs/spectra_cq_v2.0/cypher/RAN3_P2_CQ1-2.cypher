// SpectraCQ RAN3_P2_CQ1-2 (RAN3, phase 2) -- CQ1_Resolution
// Question: List the conclusions drawn at meeting RAN3#94 (meeting-outcome review).
// Gold: 15 rows, primary column "c.resolutionId"

MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#94'}) OPTIONAL MATCH (c)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN c.resolutionId, c.content, ai.agendaNumber, c.hasConsensus ORDER BY ai.agendaNumber, c.sequence LIMIT 15
