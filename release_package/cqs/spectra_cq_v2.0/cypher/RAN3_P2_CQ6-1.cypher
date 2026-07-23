// SpectraCQ RAN3_P2_CQ6-1 (RAN3, phase 2) -- CQ6
// Question: Show the resolution-count trend for agenda item 8.1 over time (topic-activity trend).
// Gold: 16 rows, primary column "m.canonicalMeetingNumber"

MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '8.1'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt AS mNum, count(r) AS cnt ORDER BY mNum ASC
