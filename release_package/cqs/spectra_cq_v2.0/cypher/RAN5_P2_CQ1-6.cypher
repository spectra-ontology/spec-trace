// SpectraCQ RAN5_P2_CQ1-6 (RAN5, phase 2) -- CQ1_Resolution
// Question: Which ten agenda items yielded the most resolutions? (busiest-agenda ranking)
// Gold: 10 rows, primary column "agenda"

MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WITH ai.agendaNumber AS agenda, ai.meetingNumber AS meeting, count(r) AS cnt ORDER BY cnt DESC, agenda, meeting LIMIT 10 RETURN agenda, meeting, cnt
