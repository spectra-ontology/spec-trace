// SpectraCQ RAN1_P2_CQ5-1 (RAN1, phase 2) -- CQ5
// Question: Trace how agreements on CSI-RS evolved over time (CSI-RS technical evolution).
// Gold: 15 rows, primary column "m.meetingNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'CSI-RS' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt ASC LIMIT 15
