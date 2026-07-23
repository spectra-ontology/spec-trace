// SpectraCQ RAN1_P2_CQ5-9 (RAN1, phase 2) -- CQ5
// Question: List the agreements on slot aggregation.
// Gold: 10 rows, primary column "m.meetingNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'slot' AND a.content CONTAINS 'aggregation' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
