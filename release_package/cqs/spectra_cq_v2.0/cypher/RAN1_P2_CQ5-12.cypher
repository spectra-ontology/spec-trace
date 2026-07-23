// SpectraCQ RAN1_P2_CQ5-12 (RAN1, phase 2) -- CQ5
// Question: What was agreed on the SSB burst set?
// Gold: 10 rows, primary column "m.meetingNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'burst' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
