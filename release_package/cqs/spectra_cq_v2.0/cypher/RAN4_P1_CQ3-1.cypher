// SpectraCQ RAN4_P1_CQ3-1 (RAN4, phase 1) -- 
// Question: Show the distribution of TDocs across agenda items (agenda workload breakdown).
// Gold: 10 rows, primary column "ai.agendaNumber"

MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
