// SpectraCQ RAN1_P2_CQ1-3 (RAN1, phase 2) -- CQ1_Resolution
// Question: List the conclusions reached at the latest meeting, RAN1#121 (status of open issues).
// Gold: 15 rows, primary column "c.resolutionId"

MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#121'}) RETURN c.resolutionId, c.content ORDER BY c.sequence, c.resolutionId LIMIT 15
