// SpectraCQ RAN1_P2_CQ5-2 (RAN1, phase 2) -- CQ5
// Question: List the agreements on HARQ feedback (HARQ decisions).
// Gold: 10 rows, primary column "m.meetingNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'HARQ' AND a.content CONTAINS 'feedback' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
