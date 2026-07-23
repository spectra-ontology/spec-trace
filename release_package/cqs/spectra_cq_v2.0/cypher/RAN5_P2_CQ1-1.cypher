// SpectraCQ RAN5_P2_CQ1-1 (RAN5, phase 2) -- CQ1_Resolution
// Question: List the conclusions reached at meeting RAN5#81 (meeting-outcome review).
// Gold: 9 rows, primary column "id"

MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN5#81'}) RETURN c.resolutionId AS id, c.content AS content, c.hasConsensus AS consensus ORDER BY c.sequence LIMIT 10
