// SpectraCQ RAN1_P2_CQ2-4 (RAN1, phase 2) -- CQ2_Tdoc-Resolution
// Question: Which agenda items carry the most resolutions? Top 10 (identifying hot topics).
// Gold: 10 rows, primary column "ai.agendaNumber"

MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(r) AS resolutionCount ORDER BY resolutionCount DESC LIMIT 10
