// SpectraCQ RAN5_P2_CQ1-2 (RAN5, phase 2) -- CQ1_Resolution
// Question: Show the number of resolutions per agenda item (agenda-outcome breakdown).
// Gold: 10 rows, primary column "agenda"

MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WITH ai.agendaNumber AS agenda, count(r) AS cnt ORDER BY cnt DESC LIMIT 10 RETURN agenda, cnt
