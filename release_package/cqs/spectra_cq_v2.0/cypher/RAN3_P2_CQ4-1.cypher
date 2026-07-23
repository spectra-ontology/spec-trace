// SpectraCQ RAN3_P2_CQ4-1 (RAN3, phase 2) -- CQ4_Moderator
// Question: Return which company moderated agenda item 8.1 (rapporteur identification).
// Gold: 10 rows, primary column "c.companyName"

MATCH (s:Summary)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '8.1'}) MATCH (s)-[:MODERATED_BY]->(c:Company) MATCH (s)-[:MADE_AT]->(m:Meeting) RETURN c.companyName, m.canonicalMeetingNumber, count(s) AS cnt ORDER BY cnt DESC, c.companyName ASC LIMIT 10
