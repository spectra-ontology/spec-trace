// SpectraCQ RAN1_P2_CQ5-13 (RAN1, phase 2) -- CQ5
// Question: List the agreements on PUCCH resources.
// Gold: 10 rows, primary column "m.meetingNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'PUCCH' AND a.content CONTAINS 'resource' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
