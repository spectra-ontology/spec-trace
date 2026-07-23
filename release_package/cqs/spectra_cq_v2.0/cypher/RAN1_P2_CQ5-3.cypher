// SpectraCQ RAN1_P2_CQ5-3 (RAN1, phase 2) -- CQ5
// Question: List the agreements on SRS configuration (SRS configuration decisions).
// Gold: 10 rows, primary column "m.meetingNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'SRS' AND a.content CONTAINS 'configuration' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
