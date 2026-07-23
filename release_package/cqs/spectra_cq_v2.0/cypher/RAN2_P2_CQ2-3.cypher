// SpectraCQ RAN2_P2_CQ2-3 (RAN2, phase 2) -- CQ2_Tdoc-Resolution
// Question: List the agreements flagging items for comeback (deferred-decision tracking).
// Gold: 8 rows, primary column "a.resolutionId"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'comeback' RETURN a.resolutionId, m.canonicalMeetingNumber, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
