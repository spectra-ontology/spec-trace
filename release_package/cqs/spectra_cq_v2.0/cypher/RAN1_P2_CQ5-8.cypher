// SpectraCQ RAN1_P2_CQ5-8 (RAN1, phase 2) -- CQ5
// Question: What was agreed on BWP switching?
// Gold: 10 rows, primary column "m.meetingNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'BWP' AND a.content CONTAINS 'switch' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
