// SpectraCQ RAN1_P2_CQ1-7 (RAN1, phase 2) -- CQ1_Resolution
// Question: What was agreed on beam management? (beam-management decisions)
// Gold: 10 rows, primary column "a.resolutionId"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'beam' AND (a.content CONTAINS 'management' OR a.content CONTAINS 'indication') RETURN a.resolutionId, m.meetingNumber, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
