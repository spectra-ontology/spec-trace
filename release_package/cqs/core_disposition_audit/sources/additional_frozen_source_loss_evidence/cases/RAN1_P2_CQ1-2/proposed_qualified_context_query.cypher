MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber:'5.1'}),
      (a)-[:MADE_AT]->(m:Meeting {meetingNumber:'RAN1#100'})
OPTIONAL MATCH (w:WorkingAssumption)-[:RESOLUTION_BELONGS_TO]->(ai), (w)-[:MADE_AT]->(m)
RETURN a.resolutionId, coalesce(a.contentWithEquations,a.content) AS content,
       a.note AS note, collect(DISTINCT {resolutionId:w.resolutionId, role:'WorkingAssumption', content:w.content}) AS qualifiedContext
ORDER BY a.sequence LIMIT 10
