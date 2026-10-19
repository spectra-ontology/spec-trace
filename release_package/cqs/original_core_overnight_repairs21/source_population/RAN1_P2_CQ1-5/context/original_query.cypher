MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.hasFFS = true RETURN a.resolutionId, a.content, m.meetingNumber ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 15
