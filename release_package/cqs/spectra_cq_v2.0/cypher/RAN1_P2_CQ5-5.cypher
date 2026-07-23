// SpectraCQ RAN1_P2_CQ5-5 (RAN1, phase 2) -- CQ5
// Question: What was agreed on PUSCH repetition? (PUSCH repetition decisions)
// Gold: 10 rows, primary column "m.meetingNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'PUSCH' AND a.content CONTAINS 'repetition' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
