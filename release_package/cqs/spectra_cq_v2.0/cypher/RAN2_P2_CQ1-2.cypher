// SpectraCQ RAN2_P2_CQ1-2 (RAN2, phase 2) -- CQ1_Resolution
// Question: List the conclusions drawn at meeting RAN2#121 (study-outcome review).
// Gold: 1 rows, primary column "c.resolutionId"

MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#121'}) RETURN c.resolutionId, c.content, c.hasConsensus ORDER BY c.sequence LIMIT 10
