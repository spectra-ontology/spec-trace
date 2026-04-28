// SpectraCQ P2_CQ2-4 — CQ2_Tdoc-Resolution추적
// Question (English): Return the top-10 agenda items by Resolution count (hotspot-topic identification).
// Schema area: classes=['AgendaItem', 'RESOLUTION_BELONGS_TO', 'Resolution'], rels=['RESOLUTION_BELONGS_TO']

MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(r) AS resolutionCount ORDER BY resolutionCount DESC LIMIT 10
