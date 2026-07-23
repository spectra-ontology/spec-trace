// SpectraCQ RAN3_P2_CQ1-3 (RAN3, phase 2) -- CQ1_Resolution
// Question: List the working assumptions from meeting RAN3#112 (provisional-decision tracking).
// Gold: 15 rows, primary column "w.resolutionId"

MATCH (w:WorkingAssumption)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#112'}) OPTIONAL MATCH (w)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN w.resolutionId, w.content, ai.agendaNumber ORDER BY ai.agendaNumber, w.sequence LIMIT 15
