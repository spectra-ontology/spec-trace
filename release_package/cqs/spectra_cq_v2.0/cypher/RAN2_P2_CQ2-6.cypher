// SpectraCQ RAN2_P2_CQ2-6 (RAN2, phase 2) -- CQ2_Tdoc-Resolution
// Question: List the agreements containing open FFS items (further-study backlog).
// Gold: 10 rows, primary column "a.resolutionId"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'FFS' RETURN a.resolutionId, m.canonicalMeetingNumber, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
