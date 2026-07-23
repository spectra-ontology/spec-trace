// SpectraCQ RAN1_P2_CQ4-1 (RAN1, phase 2) -- CQ4
// Question: Which companies led the most FL summaries under Agenda Item 7.1 (NR MIMO)? Top 5 (technical leadership).
// Gold: 5 rows, primary column "c.companyName"

MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem), (t)-[:MODERATED_BY]->(c:Company)
WHERE ai.agendaNumber STARTS WITH '7.1' AND t.summaryType = 'FL'
RETURN c.companyName, count(t) AS flCount ORDER BY flCount DESC, c.companyName LIMIT 5
