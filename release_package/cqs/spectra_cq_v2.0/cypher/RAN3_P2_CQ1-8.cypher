// SpectraCQ RAN3_P2_CQ1-8 (RAN3, phase 2) -- CQ1_Resolution
// Question: Return the top 10 agenda items by resolution count (busiest agenda areas).
// Gold: 10 rows, primary column "ai.agendaNumber"

MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(r) AS cnt ORDER BY cnt DESC, ai.agendaNumber LIMIT 10
