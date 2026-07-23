// SpectraCQ RAN1_P2_CQ5-11 (RAN1, phase 2) -- CQ5
// Question: List the agreements on DMRS patterns (DMRS pattern decisions).
// Gold: 10 rows, primary column "m.meetingNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'DMRS' AND a.content CONTAINS 'pattern' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
