// SpectraCQ RAN2_P2_CQ1-8 (RAN2, phase 2) -- CQ1_Resolution
// Question: Return the top 10 agenda items by resolution count (hot-topic ranking).
// Gold: 10 rows, primary column "ai.agendaNumber"

MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WHERE ai.agendaNumber <> 'UNKNOWN' RETURN ai.agendaNumber, ai.meetingNumber, count(r) AS resolutionCount ORDER BY resolutionCount DESC, ai.agendaNumber, ai.meetingNumber LIMIT 10
