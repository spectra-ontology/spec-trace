// SpectraCQ RAN1_P2_CQ5-7 (RAN1, phase 2) -- CQ5
// Question: List the agreements on MIMO codebooks.
// Gold: 10 rows, primary column "m.meetingNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'MIMO' AND a.content CONTAINS 'codebook' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
