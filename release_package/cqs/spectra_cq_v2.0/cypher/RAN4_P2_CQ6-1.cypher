// SpectraCQ RAN4_P2_CQ6-1 (RAN4, phase 2) -- CQ6
// Question: Show the resolution-count trend for agenda item 6.6.3 over time (topic activity trend).
// Gold: 16 rows, primary column "m.canonicalMeetingNumber"

MATCH (ai:AgendaItem) WHERE ai.agendaNumber = '6.6.3' OR ai.agendaNumber STARTS WITH '6.6.3.' MATCH (m:Meeting) WHERE m.canonicalMeetingNumber ENDS WITH ('#' + ai.meetingNumber) OPTIONAL MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai) WITH m, count(DISTINCT r) AS cnt RETURN m.canonicalMeetingNumber, m.meetingNumberInt AS mNum, cnt ORDER BY mNum ASC
