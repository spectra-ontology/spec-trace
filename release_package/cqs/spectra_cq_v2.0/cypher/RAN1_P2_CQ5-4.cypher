// SpectraCQ RAN1_P2_CQ5-4 (RAN1, phase 2) -- CQ5
// Question: What was agreed on DCI formats? (DCI format decisions)
// Gold: 10 rows, primary column "m.meetingNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'DCI' AND a.content CONTAINS 'format' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
