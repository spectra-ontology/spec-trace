// SpectraCQ RAN1_P2_CQ4-2 (RAN1, phase 2) -- CQ4
// Question: List the agenda items where Huawei served as Feature Lead on the FL summary (areas it leads).
// Gold: 15 rows, primary column "ai.agendaNumber"

MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem), (t)-[:MODERATED_BY]->(c:Company {companyName: 'Huawei'})
WHERE t.summaryType = 'FL'
RETURN DISTINCT ai.agendaNumber, count(t) AS flCount ORDER BY flCount DESC, ai.agendaNumber LIMIT 15
