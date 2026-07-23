// SpectraCQ RAN5_P1_CQ3-1 (RAN5, phase 1) -- 
// Question: Which ten agenda items drew the most TDocs? (agenda workload)
// Gold: 10 rows, primary column "ai.agendaNumber"

MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
