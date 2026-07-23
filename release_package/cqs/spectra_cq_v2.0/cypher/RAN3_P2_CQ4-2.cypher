// SpectraCQ RAN3_P2_CQ4-2 (RAN3, phase 2) -- CQ4_Moderator
// Question: List the agenda items ZTE moderated (moderator-role tracking).
// Gold: 15 rows, primary column "ai.agendaNumber"

MATCH (s:Summary)-[:MODERATED_BY]->(c:Company {companyName: 'ZTE'}) MATCH (s)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) MATCH (s)-[:MADE_AT]->(m:Meeting) RETURN ai.agendaNumber, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, ai.agendaNumber, s.summaryId LIMIT 15
