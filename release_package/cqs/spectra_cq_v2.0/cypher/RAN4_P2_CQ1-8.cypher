// SpectraCQ RAN4_P2_CQ1-8 (RAN4, phase 2) -- CQ1_Resolution
// Question: List the top 10 agenda items by number of resolutions (busiest agenda items).
// Gold: 10 rows, primary column "ai.agendaNumber"

MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(r) AS cnt ORDER BY cnt DESC LIMIT 10
